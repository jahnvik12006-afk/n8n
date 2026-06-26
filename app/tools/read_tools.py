"""READ tools — YouTube data analysis."""
import json
from datetime import date, timedelta
from app.tools.base import Tool
from app.youtube_client import youtube_data_client, youtube_analytics_client
from app.database import cache_channel, get_channel_cache, cache_video, get_video_cache


def _yt():
    return youtube_data_client()


def _ana():
    return youtube_analytics_client()


def _channel_id() -> str:
    yt = _yt()
    resp = yt.channels().list(part="id", mine=True).execute()
    return resp["items"][0]["id"]


def _date_range(days: int = 28):
    end = date.today()
    start = end - timedelta(days=days)
    return str(start), str(end)


class AnalyzeChannel(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeChannel",
            description="Channel overview: views, subscribers, watch time, upload frequency",
            permission="READ",
        )

    async def run(self, **kwargs) -> dict:
        cached = await get_channel_cache()
        if cached:
            return json.loads(cached)

        yt = _yt()
        ana = _ana()
        cid = _channel_id()

        channel = yt.channels().list(
            part="snippet,statistics,contentDetails", id=cid
        ).execute()["items"][0]

        start, end = _date_range(28)
        metrics = ana.reports().query(
            ids=f"channel=={cid}",
            startDate=start,
            endDate=end,
            metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost",
        ).execute()

        uploads = yt.playlistItems().list(
            part="id",
            playlistId=channel["contentDetails"]["relatedPlaylists"]["uploads"],
            maxResults=50,
        ).execute().get("pageInfo", {}).get("totalResults", 0)

        result = {
            "channel_id": cid,
            "title": channel["snippet"]["title"],
            "description": channel["snippet"]["description"],
            "subscribers": channel["statistics"].get("subscriberCount"),
            "total_views": channel["statistics"].get("viewCount"),
            "video_count": channel["statistics"].get("videoCount"),
            "analytics_28d": metrics.get("rows", []),
            "recent_uploads": uploads,
        }
        await cache_channel(json.dumps(result))
        return result


class AnalyzeVideos(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeVideos",
            description="List videos with performance ranking",
            permission="READ",
        )

    async def run(self, max_results: int = 20, **kwargs) -> dict:
        yt = _yt()
        cid = _channel_id()
        channel = yt.channels().list(part="contentDetails", id=cid).execute()["items"][0]
        playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

        items = yt.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=max_results,
        ).execute().get("items", [])

        video_ids = [i["contentDetails"]["videoId"] for i in items]
        stats_resp = yt.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids),
        ).execute()

        videos = []
        for v in stats_resp.get("items", []):
            videos.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "published_at": v["snippet"]["publishedAt"],
                "views": int(v["statistics"].get("viewCount", 0)),
                "likes": int(v["statistics"].get("likeCount", 0)),
                "comments": int(v["statistics"].get("commentCount", 0)),
                "tag_count": len(v["snippet"].get("tags", [])),
                "desc_len": len(v["snippet"].get("description", "")),
            })

        videos.sort(key=lambda x: x["views"], reverse=True)
        return {"videos": videos, "total": len(videos)}


class AnalyzeVideo(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeVideo",
            description="Single video audit: SEO, CTR, performance",
            permission="READ",
        )

    async def run(self, video_id: str, **kwargs) -> dict:
        cached = await get_video_cache(video_id)
        if cached:
            return json.loads(cached)

        yt = _yt()
        ana = _ana()
        cid = _channel_id()

        video = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id,
        ).execute()["items"][0]

        start, end = _date_range(28)
        try:
            analytics = ana.reports().query(
                ids=f"channel=={cid}",
                startDate=start,
                endDate=end,
                metrics="views,estimatedMinutesWatched,averageViewDuration,clickThroughRate",
                filters=f"video=={video_id}",
            ).execute()
        except Exception:
            analytics = {}

        result = {
            "id": video_id,
            "title": video["snippet"]["title"],
            "description": video["snippet"]["description"],
            "tags": video["snippet"].get("tags", []),
            "published_at": video["snippet"]["publishedAt"],
            "duration": video["contentDetails"]["duration"],
            "views": int(video["statistics"].get("viewCount", 0)),
            "likes": int(video["statistics"].get("likeCount", 0)),
            "comments": int(video["statistics"].get("commentCount", 0)),
            "analytics": analytics.get("rows", []),
        }
        await cache_video(video_id, json.dumps(result))
        return result


class AnalyzeRetention(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeRetention",
            description="Audience retention: drop points, hook analysis",
            permission="READ",
        )

    async def run(self, video_id: str | None = None, **kwargs) -> dict:
        ana = _ana()
        cid = _channel_id()
        start, end = _date_range(28)

        params = dict(
            ids=f"channel=={cid}",
            startDate=start,
            endDate=end,
            metrics="averageViewDuration,averageViewPercentage",
            dimensions="day",
        )
        if video_id:
            params["filters"] = f"video=={video_id}"

        result = ana.reports().query(**params).execute()
        return {"retention_data": result.get("rows", []), "headers": result.get("columnHeaders", [])}


class AnalyzeCTR(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeCTR",
            description="CTR analysis and trend",
            permission="READ",
        )

    async def run(self, **kwargs) -> dict:
        ana = _ana()
        cid = _channel_id()
        start, end = _date_range(28)

        result = ana.reports().query(
            ids=f"channel=={cid}",
            startDate=start,
            endDate=end,
            metrics="views,estimatedMinutesWatched,subscribersGained",
            dimensions="day",
        ).execute()
        return {"ctr_data": result.get("rows", []), "headers": result.get("columnHeaders", [])}


class AnalyzeAudience(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeAudience",
            description="Audience: geography, devices, new vs returning",
            permission="READ",
        )

    async def run(self, **kwargs) -> dict:
        ana = _ana()
        cid = _channel_id()
        start, end = _date_range(28)

        geo = ana.reports().query(
            ids=f"channel=={cid}",
            startDate=start,
            endDate=end,
            metrics="views",
            dimensions="country",
            sort="-views",
            maxResults=10,
        ).execute()

        devices = ana.reports().query(
            ids=f"channel=={cid}",
            startDate=start,
            endDate=end,
            metrics="views",
            dimensions="deviceType",
        ).execute()

        return {
            "geography": geo.get("rows", []),
            "devices": devices.get("rows", []),
        }


class AnalyzeGrowth(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeGrowth",
            description="Growth trend: subscribers and views over time",
            permission="READ",
        )

    async def run(self, days: int = 28, **kwargs) -> dict:
        ana = _ana()
        cid = _channel_id()
        start, end = _date_range(days)

        result = ana.reports().query(
            ids=f"channel=={cid}",
            startDate=start,
            endDate=end,
            metrics="views,subscribersGained,subscribersLost",
            dimensions="day",
        ).execute()
        return {"growth_data": result.get("rows", []), "headers": result.get("columnHeaders", [])}


class AnalyzeSEO(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeSEO",
            description="SEO audit: title, description, tags quality",
            permission="READ",
        )

    async def run(self, max_videos: int = 10, **kwargs) -> dict:
        yt = _yt()
        cid = _channel_id()
        channel = yt.channels().list(part="contentDetails", id=cid).execute()["items"][0]
        playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

        items = yt.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=max_videos,
        ).execute().get("items", [])

        video_ids = [i["contentDetails"]["videoId"] for i in items]
        videos_resp = yt.videos().list(
            part="snippet",
            id=",".join(video_ids),
        ).execute()

        seo_data = []
        for v in videos_resp.get("items", []):
            snip = v["snippet"]
            seo_data.append({
                "id": v["id"],
                "title": snip["title"],
                "title_length": len(snip["title"]),
                "description_length": len(snip.get("description", "")),
                "tag_count": len(snip.get("tags", [])),
                "tags": snip.get("tags", []),
            })
        return {"seo_data": seo_data}


class AnalyzeCompetitors(Tool):
    def __init__(self):
        super().__init__(
            name="AnalyzeCompetitors",
            description="Competitor metadata, views, upload patterns",
            permission="READ",
        )

    async def run(self, channel_ids: list[str], **kwargs) -> dict:
        yt = _yt()
        channels_resp = yt.channels().list(
            part="snippet,statistics",
            id=",".join(channel_ids),
        ).execute()

        competitors = []
        for ch in channels_resp.get("items", []):
            playlist_id = yt.channels().list(
                part="contentDetails", id=ch["id"]
            ).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            recent = yt.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=10,
            ).execute().get("items", [])

            video_ids = [i["contentDetails"]["videoId"] for i in recent]
            vids_resp = yt.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids),
            ).execute() if video_ids else {"items": []}

            competitors.append({
                "channel_id": ch["id"],
                "channel_title": ch["snippet"]["title"],
                "subscribers": ch["statistics"].get("subscriberCount"),
                "total_views": ch["statistics"].get("viewCount"),
                "recent_videos": [
                    {
                        "title": v["snippet"]["title"],
                        "published_at": v["snippet"]["publishedAt"],
                        "views": int(v["statistics"].get("viewCount", 0)),
                        "tags": v["snippet"].get("tags", []),
                    }
                    for v in vids_resp.get("items", [])
                ],
            })
        return {"competitors": competitors}

"""Tool registry."""
from app.tools.read_tools import (
    AnalyzeChannel, AnalyzeVideos, AnalyzeVideo,
    AnalyzeRetention, AnalyzeCTR, AnalyzeAudience,
    AnalyzeGrowth, AnalyzeSEO, AnalyzeCompetitors,
)
from app.tools.generate_tools import (
    GenerateTitles, GenerateDescriptions, GenerateTags,
    GenerateSeriesIdeas, GenerateContentStrategy, AuditSEO,
)
from app.tools.write_tools import UpdateTitle, UpdateDescription, UpdateTags
from app.tools.download_tool import FetchDownloadFormats
from app.tools.extra_tools import (
    GenerateViralHook, GenerateThumbnailText, CompareTitles,
    GenerateShortsIdeas, GenerateCommentReplies, GenerateDailyBrief, SpyCompetitor,
)

TOOLS: dict = {
    t.name: t for t in [
        AnalyzeChannel(), AnalyzeVideos(), AnalyzeVideo(),
        AnalyzeRetention(), AnalyzeCTR(), AnalyzeAudience(),
        AnalyzeGrowth(), AnalyzeSEO(), AnalyzeCompetitors(),
        GenerateTitles(), GenerateDescriptions(), GenerateTags(),
        GenerateSeriesIdeas(), GenerateContentStrategy(), AuditSEO(),
        UpdateTitle(), UpdateDescription(), UpdateTags(),
        FetchDownloadFormats(),
        GenerateViralHook(), GenerateThumbnailText(), CompareTitles(),
        GenerateShortsIdeas(), GenerateCommentReplies(), GenerateDailyBrief(),
        SpyCompetitor(),
    ]
}

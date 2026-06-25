"""Tool registry."""
from app.tools.read_tools import (
    AnalyzeChannel, AnalyzeVideos, AnalyzeVideo,
    AnalyzeRetention, AnalyzeCTR, AnalyzeAudience,
    AnalyzeGrowth, AnalyzeSEO, AnalyzeCompetitors,
)
from app.tools.generate_tools import (
    GenerateTitles, GenerateDescriptions, GenerateTags,
    GenerateSeriesIdeas, GenerateContentStrategy,
)
from app.tools.write_tools import UpdateTitle, UpdateDescription, UpdateTags

TOOLS: dict = {
    t.name: t for t in [
        AnalyzeChannel(), AnalyzeVideos(), AnalyzeVideo(),
        AnalyzeRetention(), AnalyzeCTR(), AnalyzeAudience(),
        AnalyzeGrowth(), AnalyzeSEO(), AnalyzeCompetitors(),
        GenerateTitles(), GenerateDescriptions(), GenerateTags(),
        GenerateSeriesIdeas(), GenerateContentStrategy(),
        UpdateTitle(), UpdateDescription(), UpdateTags(),
    ]
}

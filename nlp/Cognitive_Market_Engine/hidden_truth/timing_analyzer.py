"""
TIMING ANALYZER — Why was this released NOW?

Analyzes the strategic timing of news releases:
- Market hours vs after-hours releases
- Proximity to options expiry / FOMC / key events
- Friday afternoon "news dump" patterns
- Pre-positioning detection
- Calendar-aware context
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TimingAnalysis:
    """Result of timing analysis."""
    release_time: str = ""
    market_session: str = ""       # pre-market, market-hours, after-hours, weekend
    
    # Timing scores
    strategic_timing_score: float = 0.0   # 0=normal, 1=highly strategic
    news_dump_probability: float = 0.0     # Friday afternoon / holiday eve
    pre_positioning_risk: float = 0.0      # Released to allow insider positioning
    
    # Context
    proximity_events: List[Dict] = field(default_factory=list)
    timing_flags: List[str] = field(default_factory=list)
    explanation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "release_time": self.release_time,
            "market_session": self.market_session,
            "strategic_timing_score": round(self.strategic_timing_score, 3),
            "news_dump_probability": round(self.news_dump_probability, 3),
            "pre_positioning_risk": round(self.pre_positioning_risk, 3),
            "proximity_events": self.proximity_events,
            "timing_flags": self.timing_flags,
            "explanation": self.explanation,
        }


class TimingAnalyzer:
    """
    Analyzes the strategic timing of news releases.
    
    Key insight: WHEN something is said can be as important as WHAT is said.
    """
    
    # Key recurring events (approximate dates)
    RECURRING_EVENTS = {
        "fomc": {"frequency": "6_weeks", "importance": 0.95},
        "nfp": {"frequency": "monthly_first_friday", "importance": 0.85},
        "cpi": {"frequency": "monthly", "importance": 0.80},
        "gdp": {"frequency": "quarterly", "importance": 0.80},
        "opex": {"frequency": "monthly_third_friday", "importance": 0.75},
        "quad_witching": {"frequency": "quarterly_third_friday", "importance": 0.90},
        "earnings_season": {"frequency": "quarterly", "importance": 0.80},
        "ecb_meeting": {"frequency": "6_weeks", "importance": 0.85},
        "boj_meeting": {"frequency": "8_times_year", "importance": 0.75},
        "jackson_hole": {"frequency": "annual_august", "importance": 0.90},
        "g20": {"frequency": "annual", "importance": 0.70},
    }
    
    # US market hours (ET)
    MARKET_OPEN_HOUR = 9   # 9:30 AM ET
    MARKET_CLOSE_HOUR = 16  # 4:00 PM ET
    PRE_MARKET_START = 4    # 4:00 AM ET
    AFTER_HOURS_END = 20    # 8:00 PM ET
    
    def __init__(self):
        """Initialize TimingAnalyzer."""
        print("[TIMING] Analyzer initialized")
    
    def analyze(self, release_time: str = None, 
                event_type: str = None,
                source: str = None) -> TimingAnalysis:
        """
        Analyze the timing of a news release.
        
        Args:
            release_time: ISO format timestamp of release
            event_type: Type of news event
            source: Source of the news
            
        Returns:
            TimingAnalysis with strategic timing assessment
        """
        if release_time:
            try:
                dt = datetime.fromisoformat(release_time.replace("Z", "+00:00").replace("+00:00", ""))
            except (ValueError, AttributeError):
                dt = datetime.now()
        else:
            dt = datetime.now()
        
        analysis = TimingAnalysis(release_time=dt.isoformat())
        
        # Determine market session
        analysis.market_session = self._get_market_session(dt)
        
        # Check for news dump timing
        analysis.news_dump_probability = self._check_news_dump(dt)
        
        # Check proximity to key events
        analysis.proximity_events = self._check_event_proximity(dt)
        
        # Check for pre-positioning risk
        analysis.pre_positioning_risk = self._check_pre_positioning(dt, event_type)
        
        # Gather timing flags
        analysis.timing_flags = self._get_timing_flags(dt, event_type, source)
        
        # Calculate overall strategic timing score
        analysis.strategic_timing_score = self._compute_strategic_score(analysis)
        
        # Generate explanation
        analysis.explanation = self._generate_explanation(analysis)
        
        return analysis
    
    def _get_market_session(self, dt: datetime) -> str:
        """Determine which market session the release falls in."""
        hour = dt.hour
        weekday = dt.weekday()  # 0=Monday, 6=Sunday
        
        if weekday >= 5:
            return "weekend"
        
        if hour < self.PRE_MARKET_START:
            return "overnight"
        elif hour < self.MARKET_OPEN_HOUR:
            return "pre-market"
        elif hour < self.MARKET_CLOSE_HOUR:
            return "market-hours"
        elif hour < self.AFTER_HOURS_END:
            return "after-hours"
        else:
            return "overnight"
    
    def _check_news_dump(self, dt: datetime) -> float:
        """
        Check if this is a "news dump" - releasing bad news when
        nobody is watching.
        
        Classic patterns:
        - Friday afternoon (after 4 PM)
        - Before holiday weekends
        - Late night releases
        """
        score = 0.0
        weekday = dt.weekday()
        hour = dt.hour
        
        # Friday afternoon (classic news dump)
        if weekday == 4 and hour >= 16:
            score += 0.6
        
        # Friday evening
        if weekday == 4 and hour >= 20:
            score += 0.2
        
        # Saturday (extreme news dump)
        if weekday == 5:
            score += 0.4
        
        # Late night any day
        if hour >= 22 or hour < 5:
            score += 0.2
        
        # Day before major US holidays (dynamically computed)
        month, day = dt.month, dt.day
        year = dt.year
        
        # Static holiday eves
        holiday_eves = [
            (12, 24),  # Christmas Eve
            (7, 3),    # Day before July 4th
            (12, 31),  # New Year's Eve
        ]
        
        # Dynamically compute day before Thanksgiving (4th Thursday of November)
        if month == 11:
            # Find 4th Thursday: first Thursday + 21 days
            import calendar
            cal = calendar.Calendar()
            thursdays = [d for d in cal.itermonthdays2(year, 11) if d[0] != 0 and d[1] == 3]
            if len(thursdays) >= 4:
                thanksgiving_day = thursdays[3][0]
                day_before_thanksgiving = thanksgiving_day - 1
                if day == day_before_thanksgiving:
                    score += 0.5
        
        if (month, day) in holiday_eves:
            score += 0.5
        
        return min(1.0, score)
    
    def _check_event_proximity(self, dt: datetime) -> List[Dict]:
        """Check proximity to major scheduled events."""
        events = []
        
        # Check day of week for recurring events
        weekday = dt.weekday()
        day = dt.day
        month = dt.month
        
        # Monthly first Friday = NFP day
        if weekday == 4 and day <= 7:
            events.append({
                "event": "Non-Farm Payrolls",
                "proximity": "same_day",
                "importance": 0.85,
                "implication": "Released on NFP day — may be designed to amplify or counteract jobs data"
            })
        
        # Monthly third Friday = Options Expiry
        if weekday == 4 and 15 <= day <= 21:
            events.append({
                "event": "Options Expiry",
                "proximity": "same_day",
                "importance": 0.75,
                "implication": "Released on OPEX — could influence options positioning and gamma exposure"
            })
        
        # Quarterly third Friday (Mar, Jun, Sep, Dec) = Quad Witching
        if weekday == 4 and 15 <= day <= 21 and month in (3, 6, 9, 12):
            events.append({
                "event": "Quadruple Witching",
                "proximity": "same_day",
                "importance": 0.90,
                "implication": "Released during quad witching — maximum options/futures convexity"
            })
        
        # FOMC weeks (typically Tue-Wed, ~every 6 weeks)
        if weekday in (1, 2):
            events.append({
                "event": "Potential FOMC Meeting Week",
                "proximity": "possible_same_week",
                "importance": 0.70,
                "implication": "If this is an FOMC week, release timing may be strategic"
            })
        
        # Earnings season (first 3 weeks of Jan, Apr, Jul, Oct)
        if day <= 21 and month in (1, 4, 7, 10):
            events.append({
                "event": "Earnings Season",
                "proximity": "ongoing",
                "importance": 0.65,
                "implication": "Released during earnings season — may compete for attention"
            })
        
        # August = Jackson Hole month
        if month == 8 and 18 <= day <= 28:
            events.append({
                "event": "Jackson Hole Symposium",
                "proximity": "same_week",
                "importance": 0.85,
                "implication": "Near Jackson Hole — may be pre-positioning for central bank speeches"
            })
        
        return events
    
    def _check_pre_positioning(self, dt: datetime, event_type: str) -> float:
        """Estimate pre-positioning risk based on timing."""
        risk = 0.0
        
        session = self._get_market_session(dt)
        
        # After-hours releases of material info = higher pre-positioning risk
        if session in ("after-hours", "overnight", "weekend"):
            risk += 0.3
            
            # Especially for market-moving event types
            if event_type in ("earnings", "rate_decision", "policy_announcement"):
                risk += 0.2
        
        # Pre-market: less risk (market opens soon)
        if session == "pre-market":
            risk += 0.1
        
        # Friday releases of bad news = pre-positioning for Monday
        if dt.weekday() == 4 and dt.hour >= 16:
            risk += 0.2
        
        return min(1.0, risk)
    
    def _get_timing_flags(self, dt: datetime, event_type: str, 
                          source: str) -> List[str]:
        """Generate specific timing flags."""
        flags = []
        
        session = self._get_market_session(dt)
        weekday = dt.weekday()
        hour = dt.hour
        
        if session == "weekend":
            flags.append("WEEKEND_RELEASE: Released on weekend when markets are closed")
        
        if session == "after-hours":
            flags.append("AFTER_HOURS: Released after market close")
        
        if session == "overnight":
            flags.append("OVERNIGHT: Released in overnight session")
        
        if weekday == 4 and hour >= 16:
            flags.append("FRIDAY_DUMP: Classic news dump timing — Friday afternoon")
        
        if weekday == 0 and hour < 8:
            flags.append("MONDAY_AMBUSH: Early Monday release before market participants prepare")
        
        if event_type in ("earnings",) and session != "after-hours":
            flags.append("UNUSUAL_EARNINGS_TIMING: Earnings typically released after-hours")
        
        if source and source.lower() in ("fed", "ecb", "boe"):
            if hour < 8 or hour > 18:
                flags.append("UNUSUAL_CB_TIMING: Central bank communication outside normal hours")
        
        return flags
    
    def _compute_strategic_score(self, analysis: TimingAnalysis) -> float:
        """Compute overall strategic timing score."""
        components = [
            analysis.news_dump_probability * 0.30,
            analysis.pre_positioning_risk * 0.25,
            len(analysis.proximity_events) * 0.10,
            len(analysis.timing_flags) * 0.08,
        ]
        
        # Session bonus
        session_scores = {
            "market-hours": 0.0,
            "pre-market": 0.05,
            "after-hours": 0.15,
            "overnight": 0.20,
            "weekend": 0.25,
        }
        components.append(session_scores.get(analysis.market_session, 0.1))
        
        return min(1.0, sum(components))
    
    def _generate_explanation(self, analysis: TimingAnalysis) -> str:
        """Generate human-readable timing explanation."""
        parts = []
        
        parts.append(f"Released during {analysis.market_session} session.")
        
        if analysis.news_dump_probability > 0.5:
            parts.append("HIGH news dump probability — release timed for minimum attention.")
        elif analysis.news_dump_probability > 0.3:
            parts.append("Moderate news dump probability.")
        
        if analysis.pre_positioning_risk > 0.5:
            parts.append("HIGH pre-positioning risk — insiders may trade before market reaction.")
        
        if analysis.proximity_events:
            events = [e["event"] for e in analysis.proximity_events[:3]]
            parts.append(f"Near key events: {', '.join(events)}.")
        
        if analysis.timing_flags:
            parts.append(f"Flags: {'; '.join(analysis.timing_flags[:3])}")
        
        return " ".join(parts)

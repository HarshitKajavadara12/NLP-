"""
Main Orchestrator: End-to-End Pipeline

The central entry point that runs the entire 7-phase NLP-driven trading pipeline.

Pipeline Flow:
Phase 1: News Ingestion & Preprocessing
  ↓
Phase 2: Cognitive Interpretation (5 participant models)
  ↓
Phase 3: Behavior Translation (apply constraints)
  ↓
Phase 4: Market Impact Aggregation (predict market-wide effects)
  ↓
Phase 5: Reality Validation (compare vs actual market data)
  ↓
Phase 6: Signal Authorization (gate + weight by credibility)
  ↓
Phase 7: Live Execution (order management, risk management, circuit breaker)
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Ensure project root on path
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Import all phases — use REAL module paths
try:
    from news_model.news_event import NewsEvent
    from news_model.parser import NewsEventParser
except ImportError:
    NewsEvent = None
    NewsEventParser = None

try:
    from participant_cognition.participant_models import (
        create_bank_participant, create_hedge_fund_participant,
        create_hft_participant, create_market_maker_participant,
        create_retail_participant,
    )
    _PARTICIPANTS_OK = True
except ImportError:
    _PARTICIPANTS_OK = False

try:
    from market_response.behavior_models import BehaviorTranslator
except ImportError:
    BehaviorTranslator = None

try:
    from market_impact.market_impact_models import BehaviorAggregator, ImpactTranslator
except ImportError:
    BehaviorAggregator = None
    ImpactTranslator = None

try:
    from reality_validation.market_reality import RealityValidator
except ImportError:
    RealityValidator = None

try:
    from signal_auth.signal_authorization import SignalAuthorizer
except ImportError:
    SignalAuthorizer = None

try:
    from execution.execution_nexus import ExecutionNexus
except ImportError:
    ExecutionNexus = None


@dataclass
class PipelineEvent:
    """Event flowing through the pipeline"""
    event_id: str
    timestamp: datetime
    source: str  # News source
    raw_text: str
    
    # Phase 1 output
    news_event: Optional[NewsEvent] = None
    
    # Phase 2 output
    cognitive_interpretations: Optional[List] = None
    
    # Phase 3 output
    behaviors: Optional[List] = None
    
    # Phase 4 output
    market_impact: Optional[Dict] = None
    
    # Phase 5 output
    validation_result: Optional[Dict] = None
    
    # Phase 6 output
    approved_signal: Optional[object] = None
    
    # Phase 7 output (optional)
    execution_result: Optional[Dict] = None
    
    # Metadata
    pipeline_status: str = "PENDING"  # PENDING, PROCESSING, VALIDATED, APPROVED, EXECUTED, REJECTED
    error_message: Optional[str] = None


class PipelineOrchestrator:
    """
    Master orchestrator for the entire 7-phase pipeline.
    
    Coordinates flow of news events through all phases,
    from raw text to live trading signals.
    """
    
    def __init__(self, config_path: str = None, live_execution: bool = False):
        """
        Initialize the pipeline.
        
        Args:
            config_path: Path to configuration file (optional)
            live_execution: Whether to execute live trades (default: False for research)
        """
        self.config_path = config_path
        self.live_execution = live_execution
        
        # Initialize components
        self.phase_1_ready = False
        self.phase_2_ready = False
        self.phase_3_ready = False
        self.phase_4_ready = False
        self.phase_5_ready = False
        self.phase_6_ready = False
        self.phase_7_ready = False
        
        # Try to initialize each phase
        try:
            self.initialize_phases()
        except Exception as e:
            print(f"Error initializing phases: {e}")
    
    def initialize_phases(self):
        """Initialize all pipeline phases"""
        # Phase 1: News parsing
        self.phase_1_ready = (NewsEvent is not None or NewsEventParser is not None)
        
        # Phase 2: Participant models
        self.participants = []
        if _PARTICIPANTS_OK:
            try:
                self.participants = [
                    create_bank_participant(),
                    create_hedge_fund_participant(),
                    create_hft_participant(),
                    create_market_maker_participant(),
                    create_retail_participant(),
                ]
            except Exception:
                pass
        self.phase_2_ready = bool(self.participants)

        # Phase 3: Behavior translation
        if BehaviorTranslator is not None:
            try:
                self.behavior_translator = BehaviorTranslator()
                self.phase_3_ready = True
            except Exception:
                pass
        
        # Phase 4: Market impact
        if BehaviorAggregator is not None and ImpactTranslator is not None:
            try:
                self.behavior_aggregator = BehaviorAggregator()
                self.impact_translator = ImpactTranslator()
                self.phase_4_ready = True
            except Exception:
                pass
        
        # Phase 5: Reality validation
        if RealityValidator is not None:
            try:
                self.reality_validator = RealityValidator()
                self.phase_5_ready = True
            except Exception:
                pass
        
        # Phase 6: Signal authorization
        if SignalAuthorizer is not None:
            try:
                self.signal_authorizer = SignalAuthorizer()
                self.phase_6_ready = True
            except Exception:
                pass
        
        # Phase 7: Execution (optional)
        if ExecutionNexus is not None:
            try:
                self.execution_nexus = ExecutionNexus()
                self.phase_7_ready = self.live_execution
            except Exception:
                pass
    
    # ========================================================================
    # PHASE 1: News Ingestion & Preprocessing
    # ========================================================================
    
    def process_news_event(self, raw_text: str, source: str) -> PipelineEvent:
        """
        PHASE 1: Process raw news text into structured event.
        
        Args:
            raw_text: Raw news article text
            source: News source (Reuters, Bloomberg, etc.)
        
        Returns:
            PipelineEvent with Phase 1 output
        """
        try:
            event_id = f"EVT_{datetime.now().timestamp()}"
            
            # Phase 1: Parse and structure news
            if NewsEventParser is not None:
                parser = NewsEventParser()
                news_event = parser.parse(
                    timestamp_utc=datetime.now(),
                    source=source,
                    raw_text=raw_text
                )
            elif NewsEvent is not None:
                news_event = NewsEvent(raw_text=raw_text, source=source)
            else:
                raise RuntimeError("NewsEvent/Parser not available")
            
            pipeline_event = PipelineEvent(
                event_id=event_id,
                timestamp=datetime.now(),
                source=source,
                raw_text=raw_text,
                news_event=news_event,
                pipeline_status="PHASE_1_COMPLETE",
            )
            
            return pipeline_event
        
        except Exception as e:
            return PipelineEvent(
                event_id=f"EVT_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                source=source,
                raw_text=raw_text,
                pipeline_status="REJECTED",
                error_message=f"Phase 1 error: {str(e)}",
            )
    
    # ========================================================================
    # PHASE 2: Cognitive Interpretation
    # ========================================================================
    
    def interpret_cognitively(self, pipeline_event: PipelineEvent) -> PipelineEvent:
        """
        PHASE 2: Interpret news through 5 cognitive participant models.
        
        Args:
            pipeline_event: Event from Phase 1
        
        Returns:
            Updated event with Phase 2 output
        """
        if not self.phase_2_ready or pipeline_event.news_event is None:
            pipeline_event.pipeline_status = "PHASE_2_SKIPPED"
            return pipeline_event
        
        try:
            # Phase 2: Generate 5 cognitive interpretations
            interpretations = []
            for participant in self.participants:
                try:
                    expectation = participant.interpret(pipeline_event.news_event)
                    interpretations.append(expectation)
                except Exception:
                    pass
            
            pipeline_event.cognitive_interpretations = interpretations
            pipeline_event.pipeline_status = "PHASE_2_COMPLETE"
            
            return pipeline_event
        
        except Exception as e:
            pipeline_event.pipeline_status = "REJECTED"
            pipeline_event.error_message = f"Phase 2 error: {str(e)}"
            return pipeline_event
    
    # ========================================================================
    # PHASE 3: Behavior Translation
    # ========================================================================
    
    def translate_to_behavior(self, pipeline_event: PipelineEvent) -> PipelineEvent:
        """
        PHASE 3: Translate cognitive interpretations into behaviors.
        
        Args:
            pipeline_event: Event from Phase 2
        
        Returns:
            Updated event with Phase 3 output
        """
        if not self.phase_3_ready or pipeline_event.cognitive_interpretations is None:
            pipeline_event.pipeline_status = "PHASE_3_SKIPPED"
            return pipeline_event
        
        try:
            # Phase 3: Translate to behaviors
            behaviors = []
            for interpretation in pipeline_event.cognitive_interpretations:
                behavior = self.behavior_translator.translate(interpretation)
                behaviors.append(behavior)
            
            pipeline_event.behaviors = behaviors
            pipeline_event.pipeline_status = "PHASE_3_COMPLETE"
            
            return pipeline_event
        
        except Exception as e:
            pipeline_event.pipeline_status = "REJECTED"
            pipeline_event.error_message = f"Phase 3 error: {str(e)}"
            return pipeline_event
    
    # ========================================================================
    # PHASE 4: Market Impact Aggregation
    # ========================================================================
    
    def aggregate_market_impact(self, pipeline_event: PipelineEvent) -> PipelineEvent:
        """
        PHASE 4: Aggregate individual behaviors into market-wide impact.
        
        Args:
            pipeline_event: Event from Phase 3
        
        Returns:
            Updated event with Phase 4 output
        """
        if not self.phase_4_ready or pipeline_event.behaviors is None:
            pipeline_event.pipeline_status = "PHASE_4_SKIPPED"
            return pipeline_event
        
        try:
            # Phase 4: Aggregate behaviors
            aggregated = self.behavior_aggregator.aggregate(pipeline_event.behaviors)
            
            # Translate to market impact
            impact = self.impact_translator.translate(aggregated)
            
            pipeline_event.market_impact = {
                "aggregated": aggregated,
                "impact": impact,
            }
            pipeline_event.pipeline_status = "PHASE_4_COMPLETE"
            
            return pipeline_event
        
        except Exception as e:
            pipeline_event.pipeline_status = "REJECTED"
            pipeline_event.error_message = f"Phase 4 error: {str(e)}"
            return pipeline_event
    
    # ========================================================================
    # PHASE 5: Reality Validation
    # ========================================================================
    
    def validate_against_reality(
        self,
        pipeline_event: PipelineEvent,
        actual_market_data: Dict
    ) -> PipelineEvent:
        """
        PHASE 5: Validate predictions against actual market data.
        
        Args:
            pipeline_event: Event from Phase 4
            actual_market_data: Real market data (price, vol, etc.)
        
        Returns:
            Updated event with Phase 5 output
        """
        if not self.phase_5_ready or pipeline_event.market_impact is None:
            pipeline_event.pipeline_status = "PHASE_5_SKIPPED"
            return pipeline_event
        
        try:
            # Phase 5: Validate against reality
            validation = self.reality_validator.validate(
                predicted=pipeline_event.market_impact,
                actual=actual_market_data,
            )
            
            pipeline_event.validation_result = {
                "validation": validation,
                "credibility_scores": validation.get("credibility_scores", {}),
            }
            pipeline_event.pipeline_status = "PHASE_5_COMPLETE"
            
            return pipeline_event
        
        except Exception as e:
            pipeline_event.pipeline_status = "REJECTED"
            pipeline_event.error_message = f"Phase 5 error: {str(e)}"
            return pipeline_event
    
    # ========================================================================
    # PHASE 6: Signal Authorization
    # ========================================================================
    
    def authorize_signal(self, pipeline_event: PipelineEvent) -> PipelineEvent:
        """
        PHASE 6: Gate and weight signal for execution.
        
        Only events with trust > 0.6 and valid regime are approved.
        
        Args:
            pipeline_event: Event from Phase 5
        
        Returns:
            Updated event with Phase 6 output
        """
        if not self.phase_6_ready or pipeline_event.validation_result is None:
            pipeline_event.pipeline_status = "PHASE_6_SKIPPED"
            return pipeline_event
        
        try:
            # Phase 6: Authorize signal
            approved_signal = self.signal_authorizer.authorize_signal(
                news_metadata=pipeline_event.news_event,
                validation_metrics=pipeline_event.validation_result["validation"],
                prediction=pipeline_event.market_impact["impact"],
            )
            
            pipeline_event.approved_signal = approved_signal
            
            if approved_signal.status == "APPROVED":
                pipeline_event.pipeline_status = "APPROVED_FOR_EXECUTION"
            else:
                pipeline_event.pipeline_status = "FILTERED"
            
            return pipeline_event
        
        except Exception as e:
            pipeline_event.pipeline_status = "REJECTED"
            pipeline_event.error_message = f"Phase 6 error: {str(e)}"
            return pipeline_event
    
    # ========================================================================
    # PHASE 7: Execution (Optional)
    # ========================================================================
    
    def execute_signal(
        self,
        pipeline_event: PipelineEvent,
        current_market_price: float
    ) -> PipelineEvent:
        """
        PHASE 7: Execute approved signal in live market.
        
        Args:
            pipeline_event: Event from Phase 6 (approved)
            current_market_price: Current market price
        
        Returns:
            Updated event with Phase 7 output
        """
        if not self.phase_7_ready or pipeline_event.approved_signal is None:
            pipeline_event.pipeline_status = "EXECUTION_SKIPPED"
            return pipeline_event
        
        if pipeline_event.approved_signal.status != "APPROVED":
            pipeline_event.pipeline_status = "EXECUTION_BLOCKED"
            return pipeline_event
        
        try:
            # Phase 7: Execute
            execution_result = self.execution_nexus.execute_signal(
                signal=pipeline_event.approved_signal,
                current_price=current_market_price,
                current_time=datetime.now(),
            )
            
            pipeline_event.execution_result = execution_result
            pipeline_event.pipeline_status = "EXECUTED"
            
            return pipeline_event
        
        except Exception as e:
            pipeline_event.pipeline_status = "EXECUTION_FAILED"
            pipeline_event.error_message = f"Phase 7 error: {str(e)}"
            return pipeline_event
    
    # ========================================================================
    # MAIN PIPELINE ENTRY POINT
    # ========================================================================
    
    def run_full_pipeline(
        self,
        raw_news: str,
        source: str,
        actual_market_data: Dict = None,
        current_market_price: float = None,
    ) -> PipelineEvent:
        """
        Run the entire 7-phase pipeline from raw news to execution.
        
        Args:
            raw_news: Raw news article text
            source: News source
            actual_market_data: Actual market behavior (for validation)
            current_market_price: Current market price (for execution)
        
        Returns:
            PipelineEvent with complete pipeline results
        """
        # Phase 1: Parse news
        event = self.process_news_event(raw_news, source)
        
        if event.pipeline_status == "REJECTED":
            return event
        
        # Phase 2: Interpret cognitively
        event = self.interpret_cognitively(event)
        
        if event.pipeline_status == "REJECTED":
            return event
        
        # Phase 3: Translate to behavior
        event = self.translate_to_behavior(event)
        
        if event.pipeline_status == "REJECTED":
            return event
        
        # Phase 4: Aggregate market impact
        event = self.aggregate_market_impact(event)
        
        if event.pipeline_status == "REJECTED":
            return event
        
        # Phase 5: Validate against reality (if data provided)
        if actual_market_data:
            event = self.validate_against_reality(event, actual_market_data)
            
            if event.pipeline_status == "REJECTED":
                return event
            
            # Phase 6: Authorize signal
            event = self.authorize_signal(event)
            
            if event.pipeline_status == "REJECTED":
                return event
            
            # Phase 7: Execute signal (if approved and price provided)
            if (event.pipeline_status == "APPROVED_FOR_EXECUTION" and
                current_market_price is not None and
                self.live_execution):
                event = self.execute_signal(event, current_market_price)
        
        return event
    
    # ========================================================================
    # REPORTING & DIAGNOSTICS
    # ========================================================================
    
    def get_pipeline_status(self) -> Dict:
        """Get status of all phases"""
        return {
            "phase_1": "READY" if self.phase_1_ready else "NOT_READY",
            "phase_2": "READY" if self.phase_2_ready else "NOT_READY",
            "phase_3": "READY" if self.phase_3_ready else "NOT_READY",
            "phase_4": "READY" if self.phase_4_ready else "NOT_READY",
            "phase_5": "READY" if self.phase_5_ready else "NOT_READY",
            "phase_6": "READY" if self.phase_6_ready else "NOT_READY",
            "phase_7": "READY" if self.phase_7_ready else "NOT_READY",
        }
    
    def print_pipeline_summary(self, event: PipelineEvent) -> None:
        """Print summary of event through pipeline"""
        print(f"""
                                                                 
            7-PHASE PIPELINE EXECUTION SUMMARY                  
                                                                 

Event ID:           {event.event_id}
Timestamp:          {event.timestamp}
Source:             {event.source}
Final Status:       {event.pipeline_status}

Phase 1 (News):     {' ' if event.news_event else ' ️'}
Phase 2 (Cognitive): {' ' if event.cognitive_interpretations else ' ️'}
Phase 3 (Behavior): {' ' if event.behaviors else ' ️'}
Phase 4 (Impact):   {' ' if event.market_impact else ' ️'}
Phase 5 (Validate): {' ' if event.validation_result else ' ️'}
Phase 6 (Authorize):{' ' if event.approved_signal else ' ️'}
Phase 7 (Execute):  {' ' if event.execution_result else ' ️'}

{f'Error: {event.error_message}' if event.error_message else 'No errors'}
""")


# ============================================================================
# ENTRY POINT: Main Function
# ============================================================================

if __name__ == "__main__":
    """
    Example usage of the complete pipeline.
    """
    
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(live_execution=False)
    
    # Check status
    print("Pipeline Status:", orchestrator.get_pipeline_status())
    
    # Example news
    sample_news = """
    Apple Inc announced better-than-expected Q1 earnings with strong iPhone sales
    and services revenue growth. The company also announced a $50B buyback program.
    Analysts expect positive momentum in the near term.
    """
    
    # Run full pipeline
    result = orchestrator.run_full_pipeline(
        raw_news=sample_news,
        source="reuters",
        # actual_market_data would come from real market data feed
        # current_market_price would come from live price feed
    )
    
    # Print summary
    orchestrator.print_pipeline_summary(result)

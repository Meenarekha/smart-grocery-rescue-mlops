import json
from src.feedback.feedback_manager import FeedbackManager

def test_feedback_cycle(tmp_path):
    f_path = tmp_path / "feedback.json"
    mgr = FeedbackManager(feedback_path=str(f_path))
    
    assert mgr.get_score_modifier(101, "italian") == 0.0
    
    mgr.record_feedback(101, "italian", "like")
    # Like recipe: +1.5, Like cuisine: +0.5 -> total = 2.0
    assert mgr.get_score_modifier(101, "italian") == 2.0
    
    mgr.record_feedback(101, "italian", "cooked")
    # Cooked recipe: +3.0, Cooked cuisine: +1.0 -> added 4.0 -> total = 6.0
    assert mgr.get_score_modifier(101, "italian") == 6.0
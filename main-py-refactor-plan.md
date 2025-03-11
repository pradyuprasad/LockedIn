# Refactoring Plan for main.py

## Current Issues

`main.py` currently has several responsibilities mixed together:
- Data collection (window tracking)
- User interface & CLI handling
- Session management
- Activity duration tracking

This creates maintenance challenges and makes the code harder to test and extend.

## Proposed Architecture

We'll refactor `main.py` into several distinct components:

### 1. ActivityTracker Class
```python
class ActivityTracker:
    """Core activity tracking functionality"""
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Initialize other state

    def get_active_window_info(self):
        # Extract active window info logic here
        # Returns app_name, window_title, url
    
    def track_activity(self):
        # Single iteration of activity tracking
        # Returns activity data
    
    def start_tracking(self, callback=None):
        # Main tracking loop
        # Calls callback with activity data if provided
```

### 2. SessionManager Class
```python
class SessionManager:
    """Manages tracking sessions"""
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_session = None
        self.session_start_time = None
        
    def start_session(self, name):
        # Start a new session
        
    def stop_session(self):
        # Stop current session
        
    def get_session_info(self):
        # Return current session info
```

### 3. ActivityAnalyzer Class
```python
class ActivityAnalyzer:
    """Analyzes activity data"""
    def __init__(self):
        self.activity_duration = defaultdict(int)
        
    def update_duration(self, activity_key, duration):
        # Update duration for activity
        
    def calculate_top_activities(self, limit=5):
        # Return top activities
        
    def reset(self):
        # Reset all durations
```

### 4. CLI Interface Module
- Keep CLI interface in main.py but separate from core logic
- Use the above classes for actual functionality
- Handle user input and display output

## Implementation Steps

1. Extract utility functions first
   - `format_elapsed_time()`
   - `extract_domain()`
   - `run_applescript()`
   - Browser detection functions

2. Create the `ActivityTracker` class
   - Move window tracking logic
   - Use DatabaseManager for persistence

3. Create the `SessionManager` class
   - Move session management logic
   - Interface with DatabaseManager

4. Create the `ActivityAnalyzer` class
   - Move duration tracking and analysis

5. Refactor main CLI interface
   - Use the new classes
   - Keep interface similar to maintain compatibility

## File Structure

```
tracking/
  __init__.py
  activity_tracker.py  # ActivityTracker class
  session_manager.py   # SessionManager class 
  activity_analyzer.py # ActivityAnalyzer class
  utils.py             # Utility functions

main.py                # CLI interface using the above components
```

## Testing Strategy

- Unit tests for each new class
- Integration test for the full workflow
- Manual verification of the refactored functionality

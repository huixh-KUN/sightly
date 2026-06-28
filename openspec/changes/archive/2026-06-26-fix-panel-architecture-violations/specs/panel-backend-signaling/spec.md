## ADDED Requirements

### Requirement: Panel SHALL communicate with backends exclusively through AppState signals
All Panel classes and their child GroupWidgets SHALL NOT directly call methods or read properties on `self.app.xxx_manager`, `self.app.xxx_module`, or any other backend objects. All backend communication SHALL go through AppState signals defined in `core/state.py` or Panel-level Qt signals connected in `main_window.py`.

#### Scenario: BackgroundPanel selects a target window
- **WHEN** user selects a window from WindowSelector
- **THEN** BackgroundPanel emits `window_selected(hwnd, title)` signal (not `self.app.background_manager.set_target_window()`)
- **THEN** MainWindow's connected slot calls `background_manager.set_target_window(hwnd)`

#### Scenario: BackgroundPanel loads config with auto-reconnect
- **WHEN** BackgroundPanel receives config via `set_config()` that contains `window_class`/`window_process`/`window_title`
- **THEN** BackgroundPanel emits `auto_reconnect_requested(window_class, window_process, window_title)` signal
- **THEN** MainWindow calls `background_manager.auto_reconnect()` and emits result back to panel via a signal or callback

#### Scenario: BackgroundGroupWidget reads target hwnd
- **WHEN** BackgroundGroupWidget needs current target window handle for coordinate math
- **THEN** it SHALL read from a local property set by the panel (not from `self.app.background_manager.target_hwnd`)

### Requirement: GroupEditWindow SHALL NOT pass app reference to child widgets
GroupEditWindow SHALL NOT store or forward the `app` reference to child GroupWidget classes. GroupWidgets that need backend access SHALL receive only the specific data and signal connections they need through their constructor or dedicated setters.

#### Scenario: GroupEditWindow creates a GroupWidget
- **WHEN** GroupEditWindow constructs a GroupWidget (OCRGroupWidget, ImageGroupWidget, etc.)
- **THEN** it SHALL NOT pass the `app` reference
- **THEN** it SHALL pass only the specific configuration dict and signal connections

### Requirement: SettingsPanel SHALL write config through AppState signals
SettingsPanel SHALL NOT directly access `self.app.alarm_sound_path`, `self.app.alarm_volume`, `self.app._register_shortcuts()`, or `self.app.save_config()`. All config writes SHALL be emitted as AppState signals and handled by MainWindow.

#### Scenario: SettingsPanel saves alarm configuration
- **WHEN** user modifies alarm settings in SettingsPanel
- **THEN** SettingsPanel emits a config change signal containing the new values
- **THEN** MainWindow writes the values to backend ConfigVars and calls `save_config()`

#### Scenario: SettingsPanel registers shortcuts
- **WHEN** user changes shortcut keys in SettingsPanel
- **THEN** SettingsPanel emits `shortcuts_changed(start_shortcut, stop_shortcut)` signal
- **THEN** MainWindow calls `_register_shortcuts()` with the new values

### Requirement: TimedPanel SHALL request position selection through signals
TimedGroupWidget SHALL NOT call `self.app.timed_module.start_timed_position_selection()`. It SHALL emit a signal requesting position selection, and MainWindow SHALL route it to the backend module.

#### Scenario: TimedGroupWidget selects a click position
- **WHEN** user clicks "选择位置" in TimedGroupWidget
- **THEN** TimedGroupWidget emits `position_selection_requested(group_index)` signal
- **THEN** MainWindow calls `timed_module.start_timed_position_selection()` and connects the result back to the widget

### Requirement: HomePanel SHALL trigger config save through AppState signal
HomePanel SHALL NOT call `self.app.save_config()` directly. It SHALL emit a signal that triggers MainWindow to save.

#### Scenario: HomePanel triggers config save on workspace switch
- **WHEN** HomePanel switches workspace
- **THEN** it emits a signal requesting config save
- **THEN** MainWindow saves current config before switching

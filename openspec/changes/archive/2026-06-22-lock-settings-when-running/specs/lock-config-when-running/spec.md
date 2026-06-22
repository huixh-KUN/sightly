## ADDED Requirements

### Requirement: Module switches disabled during run
When the application is in running state, all module switches on the Home page SHALL be disabled and non-interactive.

#### Scenario: Switch disabled after start
- **WHEN** `_on_start_all()` completes successfully
- **THEN** every `SwitchButton` in `HomePanel._cards` SHALL have `isEnabled()` returning `False`

#### Scenario: Switch re-enabled after stop
- **WHEN** `_on_stop_all()` completes successfully
- **THEN** every `SwitchButton` in `HomePanel._cards` SHALL have `isEnabled()` returning `True`

### Requirement: Panel editing disabled during run
When running, all monitoring group panels SHALL have their "add group" buttons and all existing group edit controls disabled.

#### Scenario: Cannot add or edit groups while running
- **WHEN** application is running
- **THEN** the "新增识别组" / "新增检测组" / "新增定时组" buttons in OCR/Background/Image/Timed/Number panels SHALL be disabled
- **AND** all `QLineEdit`, `QSpinBox`, `QComboBox`, `KeyCaptureWidget`, `DangerButton("删除")` inside existing groups SHALL be disabled

#### Scenario: Editing restored after stop
- **WHEN** `_on_stop_all()` completes successfully
- **THEN** the same widgets from the scenario above SHALL be enabled again

### Requirement: Shortcut key capture disabled during run
When running, the shortcut key modification widgets in the Settings panel SHALL be disabled.

#### Scenario: KeyCaptureWidget "修改" button disabled while running
- **WHEN** application is running
- **THEN** the `QPushButton("修改")` inside each `KeyCaptureWidget` in `GeneralSettingsCard` SHALL be disabled

#### Scenario: Key capture restored after stop
- **WHEN** `_on_stop_all()` completes successfully
- **THEN** the "修改" buttons SHALL be enabled again

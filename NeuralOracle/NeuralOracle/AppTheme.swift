import SwiftUI
import IOKit.ps

enum ThemeVariant: String, CaseIterable, Identifiable {
    case cyan = "CYAN", green = "GREEN", amber = "AMBER", red = "RED", violet = "VIOLET"
    var id: String { rawValue }
}

enum PanelPositionPreset: String, CaseIterable {
    case freeFloat = "Free", topRight = "Top Right", topLeft = "Top Left",
         bottomRight = "Bottom Right", bottomLeft = "Bottom Left", center = "Center"
}

@MainActor
@Observable
final class AppTheme {
    static let shared = AppTheme()

    var variant: ThemeVariant   = .cyan  { didSet { save() } }
    var panelOpacity: Double    = 0.85   { didSet { save() } }
    var fontSize: Double        = 12.5   { didSet { save() } }
    var positionPreset: PanelPositionPreset = .freeFloat { didSet { save() } }
    var animationsEnabled: Bool = true   // auto-managed by battery state
    var matrixEnabled: Bool     = true   { didSet { save() } }

    var primary: Color {
        switch variant {
        case .cyan:   Color(red: 0.0,  green: 0.95, blue: 0.95)
        case .green:  Color(red: 0.15, green: 0.95, blue: 0.45)
        case .amber:  Color(red: 0.95, green: 0.75, blue: 0.1)
        case .red:    Color(red: 1.0,  green: 0.25, blue: 0.35)
        case .violet: Color(red: 0.7,  green: 0.3,  blue: 1.0)
        }
    }
    var primaryDim: Color  { primary.opacity(0.55) }
    var border: Color      { primary.opacity(0.30) }
    var bg: Color          { Color(red: 0.04, green: 0.06, blue: 0.10) }
    var panel: Color       { Color(red: 0.06, green: 0.09, blue: 0.14) }
    var userMsg: Color     { Color(red: 0.95, green: 0.80, blue: 0.20) }
    var success: Color     { Color(red: 0.15, green: 0.95, blue: 0.45) }
    var danger: Color      { Color(red: 1.0,  green: 0.25, blue: 0.35) }
    var gold: Color        { Color(red: 0.95, green: 0.80, blue: 0.20) }

    var animDuration: Double { animationsEnabled ? 0.18 : 0.05 }

    private init() {
        load()
        checkPowerSource()
        // Monitor power state every 60 seconds
        Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.checkPowerSource() }
        }
    }

    private func checkPowerSource() {
        let snapshot = IOPSCopyPowerSourcesInfo().takeRetainedValue()
        let sources  = IOPSCopyPowerSourcesList(snapshot).takeRetainedValue() as [CFTypeRef]
        let onBattery = sources.contains { src in
            guard let desc = IOPSGetPowerSourceDescription(snapshot, src)?.takeUnretainedValue() as? [String: Any]
            else { return false }
            return (desc["Power Source State"] as? String) == "Battery Power"
        }
        // Disable heavy animations on battery to save CPU
        animationsEnabled = !onBattery
        if onBattery { matrixEnabled = false }
    }

    private func save() {
        let ud = UserDefaults.standard
        ud.set(variant.rawValue,       forKey: "theme.variant")
        ud.set(panelOpacity,           forKey: "theme.opacity")
        ud.set(fontSize,               forKey: "theme.fontSize")
        ud.set(positionPreset.rawValue,forKey: "theme.position")
        ud.set(matrixEnabled,          forKey: "theme.matrix")
    }

    private func load() {
        let ud = UserDefaults.standard
        if let v = ud.string(forKey: "theme.variant"), let tv = ThemeVariant(rawValue: v) { variant = tv }
        let op = ud.double(forKey: "theme.opacity");   if op > 0 { panelOpacity = max(0.2, min(1.0, op)) }
        let fs = ud.double(forKey: "theme.fontSize");  if fs > 0 { fontSize = max(10, min(20, fs)) }
        if let p = ud.string(forKey: "theme.position"), let pp = PanelPositionPreset(rawValue: p) { positionPreset = pp }
        if ud.object(forKey: "theme.matrix") != nil { matrixEnabled = ud.bool(forKey: "theme.matrix") }
    }
}

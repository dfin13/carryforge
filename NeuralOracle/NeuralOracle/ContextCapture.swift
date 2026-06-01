import AppKit
import ApplicationServices

// Snapshot of the user's active environment at hotkey time
struct AppContext {
    var appName: String      = ""
    var windowTitle: String  = ""
    var selectedText: String = ""
    var bundleID: String     = ""
    var sourceApp: NSRunningApplication?

    var isEmpty: Bool { appName.isEmpty }

    // One-line injection string for system prompts
    var promptPrefix: String {
        guard !appName.isEmpty else { return "" }
        var parts = ["Active app: \(appName)"]
        if !windowTitle.isEmpty { parts.append("window: \"\(windowTitle)\"") }
        return "[\(parts.joined(separator: ", "))] "
    }
}

enum ContextCapture {

    // MARK: - Capture current app context + selected text

    static func capture() -> AppContext {
        guard AXIsProcessTrusted() else { return AppContext() }
        let workspace = NSWorkspace.shared
        guard let app = workspace.frontmostApplication else { return AppContext() }

        var ctx = AppContext(
            appName: app.localizedName ?? "",
            bundleID: app.bundleIdentifier ?? "",
            sourceApp: app
        )

        let axApp = AXUIElementCreateApplication(app.processIdentifier)

        // Window title
        var windowRef: CFTypeRef?
        if AXUIElementCopyAttributeValue(axApp, kAXFocusedWindowAttribute as CFString, &windowRef) == .success,
           let win = windowRef {
            var titleRef: CFTypeRef?
            if AXUIElementCopyAttributeValue(win as! AXUIElement, kAXTitleAttribute as CFString, &titleRef) == .success {
                ctx.windowTitle = (titleRef as? String) ?? ""
            }
        }

        // Selected text from focused element
        ctx.selectedText = selectedText(from: axApp)
        return ctx
    }

    // MARK: - Grab selected text only (fast path for selection hotkey)

    static func captureSelectedText() -> String? {
        guard AXIsProcessTrusted() else { return nil }
        guard let app = NSWorkspace.shared.frontmostApplication else { return nil }
        let axApp = AXUIElementCreateApplication(app.processIdentifier)
        let text = selectedText(from: axApp)
        return text.isEmpty ? nil : text
    }

    // MARK: - Paste text into the source app (Cmd+V simulation)

    static func paste(_ text: String, into app: NSRunningApplication?) {
        // Save current clipboard content
        let previous = NSPasteboard.general.string(forType: .string)

        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(text, forType: .string)

        // Restore focus to source app, then simulate Cmd+V
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            app?.activate(options: .activateIgnoringOtherApps)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                simulatePaste()
                // Restore old clipboard after paste completes
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    if let previous {
                        NSPasteboard.general.clearContents()
                        NSPasteboard.general.setString(previous, forType: .string)
                    }
                }
            }
        }
    }

    // MARK: - Helpers

    private static func selectedText(from axApp: AXUIElement) -> String {
        var focusedRef: CFTypeRef?
        guard AXUIElementCopyAttributeValue(axApp, kAXFocusedUIElementAttribute as CFString, &focusedRef) == .success,
              let focused = focusedRef else { return "" }
        var selRef: CFTypeRef?
        guard AXUIElementCopyAttributeValue(focused as! AXUIElement, kAXSelectedTextAttribute as CFString, &selRef) == .success
        else { return "" }
        return (selRef as? String) ?? ""
    }

    private static func simulatePaste() {
        let src = CGEventSource(stateID: .hidSystemState)
        guard let dn = CGEvent(keyboardEventSource: src, virtualKey: 9, keyDown: true),
              let up = CGEvent(keyboardEventSource: src, virtualKey: 9, keyDown: false) else { return }
        dn.flags = .maskCommand
        up.flags = .maskCommand
        dn.post(tap: .cgAnnotatedSessionEventTap)
        up.post(tap: .cgAnnotatedSessionEventTap)
    }
}

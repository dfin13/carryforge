import SwiftUI
import AppKit

@main
struct StealthAIApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        Settings { EmptyView() }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var panelManager: PanelManager?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        panelManager = PanelManager.shared
        panelManager?.setupPanel()
        panelManager?.setupEventTap()
        panelManager?.startHealthMonitor()

        log("NeuralOracle launched", cat: "app")

        // Show onboarding on first launch
        if !UserDefaults.standard.bool(forKey: "onboarding.completed") {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.panelManager?.showPanel()
            }
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    // MARK: URL scheme: neuraloracle://query?text=...&preset=explain
    func application(_ application: NSApplication, open urls: [URL]) {
        for url in urls { handleURL(url) }
    }

    private func handleURL(_ url: URL) {
        guard url.scheme == "neuraloracle" else { return }
        let components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        let text    = components?.queryItems?.first(where: { $0.name == "text" })?.value ?? ""
        let preset  = components?.queryItems?.first(where: { $0.name == "preset" })?.value

        DispatchQueue.main.async { [weak self] in
            guard let vm = self?.panelManager?.chatVM else { return }
            if let preset {
                let cmd = "/\(preset) \(text)"
                vm.inputText = cmd
            } else {
                vm.inputText = text
            }
            self?.panelManager?.showPanel()
            if !text.isEmpty {
                Task { await vm.sendMessage() }
            }
        }
    }
}

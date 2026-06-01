import SwiftUI
import AppKit

struct OnboardingView: View {
    @AppStorage("onboarding.completed") private var completed = false
    @State private var step = 0
    @State private var connectionTested = false
    @State private var connectionOK = false
    @State private var accessibilityOK = false
    @State private var testing = false
    let onDismiss: () -> Void

    private let theme = AppTheme.shared

    var body: some View {
        ZStack {
            theme.bg.ignoresSafeArea()
            VStack(spacing: 0) {
                // Progress bar
                HStack(spacing: 4) {
                    ForEach(0..<4) { i in
                        Capsule()
                            .fill(i <= step ? theme.primary : theme.primaryDim.opacity(0.3))
                            .frame(height: 3)
                            .animation(.easeInOut(duration: 0.3), value: step)
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 20)

                Spacer()

                Group {
                    switch step {
                    case 0: welcomeStep
                    case 1: accessibilityStep
                    case 2: ollamaStep
                    case 3: readyStep
                    default: EmptyView()
                    }
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing).combined(with: .opacity),
                    removal: .move(edge: .leading).combined(with: .opacity)
                ))
                .id(step)

                Spacer()

                // Navigation
                HStack {
                    if step > 0 {
                        CyberActionButton("BACK") { withAnimation { step -= 1 } }
                    }
                    Spacer()
                    if step < 3 {
                        CyberActionButton(step == 2 && !connectionTested ? "SKIP" : "NEXT") {
                            withAnimation { step += 1 }
                        }
                    } else {
                        CyberActionButton("LAUNCH ORACLE") {
                            completed = true
                            onDismiss()
                        }
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 20)
            }
        }
        .onAppear { accessibilityOK = AXIsProcessTrusted() }
    }

    // MARK: Steps

    var welcomeStep: some View {
        VStack(spacing: 20) {
            Text("◈")
                .font(.system(size: 48))
                .foregroundStyle(theme.primary)
                .shadow(color: theme.primary.opacity(0.6), radius: 20)

            Text("NEURAL ORACLE")
                .font(.system(size: 22, weight: .bold, design: .monospaced))
                .foregroundStyle(theme.primary)
                .shadow(color: theme.primary.opacity(0.5), radius: 10)

            Text("v0.9 · LOCAL AI INTERFACE")
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(theme.primaryDim)

            VStack(alignment: .leading, spacing: 10) {
                FeatureRow(icon: "keyboard", text: "Global hotkey Cmd+Opt+L to summon from anywhere")
                FeatureRow(icon: "text.cursor",   text: "Capture selected text with Cmd+Opt+Shift+L")
                FeatureRow(icon: "arrow.turn.up.left", text: "Paste AI responses back into any app")
                FeatureRow(icon: "folder",        text: "Index local docs for context-aware answers")
                FeatureRow(icon: "clock",         text: "Full SQLite conversation history")
            }
            .padding(16)
            .background(theme.panel.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(theme.border))
        }
        .padding(.horizontal, 24)
    }

    var accessibilityStep: some View {
        VStack(spacing: 16) {
            StepHeader(icon: "accessibility", title: "ACCESSIBILITY ACCESS",
                       subtitle: "Required for global hotkeys and text capture")

            StatusRow(label: "Accessibility Permission",
                      ok: accessibilityOK,
                      detail: accessibilityOK ? "Granted" : "Not granted")

            if !accessibilityOK {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Without accessibility access, the global hotkey (Cmd+Opt+L) will not function. Neural Oracle needs this to intercept keystrokes and read selected text.")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(theme.primaryDim)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .background(theme.danger.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).strokeBorder(theme.danger.opacity(0.3)))

                CyberActionButton("OPEN SYSTEM SETTINGS") {
                    NSWorkspace.shared.open(
                        URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
                    )
                }
                CyberActionButton("CHECK AGAIN") {
                    accessibilityOK = AXIsProcessTrusted()
                }
            }

            StatusRow(label: "Screen Recording (for vision)", ok: true, detail: "Grant if using vision features")
            StatusRow(label: "Microphone (for voice input)",  ok: true, detail: "Grant on first voice use")
        }
        .padding(.horizontal, 24)
    }

    var ollamaStep: some View {
        VStack(spacing: 16) {
            StepHeader(icon: "network", title: "OLLAMA CONNECTION",
                       subtitle: "Local AI backend at localhost:11434")

            if connectionTested {
                StatusRow(label: "Ollama API", ok: connectionOK,
                          detail: connectionOK ? "Responding" : "Not responding")
            }

            if !connectionOK {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Install & start Ollama:")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(theme.primaryDim)
                    Text("  brew install ollama\n  ollama serve\n  ollama pull llama3")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(theme.primary)
                }
                .padding(12)
                .background(theme.bg.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).strokeBorder(theme.border))
            }

            CyberActionButton(testing ? "TESTING..." : "TEST CONNECTION") {
                guard !testing else { return }
                testing = true
                Task {
                    do {
                        let (_, resp) = try await URLSession.shared.data(from: URL(string: "http://localhost:11434/api/tags")!)
                        connectionOK = (resp as? HTTPURLResponse)?.statusCode == 200
                    } catch { connectionOK = false }
                    connectionTested = true
                    testing = false
                }
            }
        }
        .padding(.horizontal, 24)
    }

    var readyStep: some View {
        VStack(spacing: 20) {
            Text(connectionOK ? "✦" : "◇")
                .font(.system(size: 40))
                .foregroundStyle(connectionOK ? theme.success : theme.gold)
                .shadow(color: (connectionOK ? theme.success : theme.gold).opacity(0.5), radius: 16)

            Text(connectionOK ? "SYSTEMS ONLINE" : "READY (OFFLINE MODE)")
                .font(.system(size: 16, weight: .bold, design: .monospaced))
                .foregroundStyle(connectionOK ? theme.success : theme.gold)

            VStack(alignment: .leading, spacing: 8) {
                HintRow(key: "Cmd+Opt+L",         value: "Toggle overlay")
                HintRow(key: "Cmd+Opt+Shift+L",   value: "Capture selection + quick actions")
                HintRow(key: "Cmd+Opt+V",          value: "Open with clipboard")
                HintRow(key: "Triple Cmd+Opt+L",   value: "Debug mode")
                HintRow(key: "/help",              value: "Show slash commands")
            }
            .padding(14)
            .background(theme.panel.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(theme.border))
        }
        .padding(.horizontal, 24)
    }
}

// MARK: - Sub-components

private struct FeatureRow: View {
    let icon: String; let text: String
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon).font(.system(size: 12)).foregroundStyle(AppTheme.shared.primary).frame(width: 18)
            Text(text).font(.system(size: 11, design: .monospaced)).foregroundStyle(AppTheme.shared.primaryDim)
        }
    }
}

private struct StepHeader: View {
    let icon: String; let title: String; let subtitle: String
    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 28)).foregroundStyle(AppTheme.shared.primary)
                .shadow(color: AppTheme.shared.primary.opacity(0.5), radius: 10)
            Text(title).font(.system(size: 14, weight: .bold, design: .monospaced)).foregroundStyle(AppTheme.shared.primary)
            Text(subtitle).font(.system(size: 10, design: .monospaced)).foregroundStyle(AppTheme.shared.primaryDim)
        }
    }
}

private struct StatusRow: View {
    let label: String; let ok: Bool; let detail: String
    var body: some View {
        HStack {
            Circle().fill(ok ? AppTheme.shared.success : AppTheme.shared.danger).frame(width: 7, height: 7)
                .shadow(color: (ok ? AppTheme.shared.success : AppTheme.shared.danger).opacity(0.5), radius: 4)
            Text(label).font(.system(size: 11, design: .monospaced)).foregroundStyle(AppTheme.shared.primaryDim)
            Spacer()
            Text(detail).font(.system(size: 10, design: .monospaced))
                .foregroundStyle(ok ? AppTheme.shared.success : AppTheme.shared.danger)
        }
        .padding(.horizontal, 12).padding(.vertical, 7)
        .background(AppTheme.shared.bg.opacity(0.4))
        .clipShape(RoundedRectangle(cornerRadius: 6))
        .overlay(RoundedRectangle(cornerRadius: 6).strokeBorder(AppTheme.shared.border))
    }
}

private struct HintRow: View {
    let key: String; let value: String
    var body: some View {
        HStack {
            Text(key).font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundStyle(AppTheme.shared.primary)
            Spacer()
            Text(value).font(.system(size: 10, design: .monospaced)).foregroundStyle(AppTheme.shared.primaryDim)
        }
    }
}

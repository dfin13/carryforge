import Foundation
import PDFKit
import AppKit

struct RAGDocument: Identifiable {
    let id = UUID()
    let url: URL
    var title: String { url.lastPathComponent }
    var content: String
    var chunks: [String] = []
    var modifiedAt: Date
}

@MainActor
@Observable
final class RAGWatcher {
    static let shared = RAGWatcher()

    var documents: [RAGDocument] = []
    var watchedFolderURL: URL?    { didSet { restartWatch() } }
    var isIndexing = false
    var documentCount: Int { documents.count }

    private var eventStream: FSEventStreamRef?
    private let indexQueue = DispatchQueue(label: "com.neuraloracle.rag", qos: .utility)
    private let chunkSize = 800  // characters per chunk
    private let maxDocuments = 200

    private init() {
        if let bookmark = UserDefaults.standard.data(forKey: "rag.folderBookmark") {
            var stale = false
            watchedFolderURL = try? URL(
                resolvingBookmarkData: bookmark,
                options: .withSecurityScope,
                bookmarkDataIsStale: &stale
            )
        }
    }

    // MARK: Folder selection

    func selectFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.message = "Select a folder to index for context-aware responses"
        panel.prompt = "Watch Folder"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        url.startAccessingSecurityScopedResource()
        // Save security-scoped bookmark
        if let bookmark = try? url.bookmarkData(options: .withSecurityScope) {
            UserDefaults.standard.set(bookmark, forKey: "rag.folderBookmark")
        }
        watchedFolderURL = url
    }

    func clearFolder() {
        stopWatch()
        watchedFolderURL = nil
        documents.removeAll()
        UserDefaults.standard.removeObject(forKey: "rag.folderBookmark")
    }

    // MARK: Indexing

    func indexFolder(_ url: URL) async {
        isIndexing = true
        let supportedExts = Set(["txt", "md", "markdown", "swift", "py", "js", "ts", "go", "rs", "pdf"])
        let enumerator = FileManager.default.enumerator(
            at: url,
            includingPropertiesForKeys: [.contentModificationDateKey],
            options: [.skipsHiddenFiles, .skipsPackageDescendants]
        )

        var found: [RAGDocument] = []
        while let fileURL = enumerator?.nextObject() as? URL {
            guard found.count < maxDocuments else { break }
            guard supportedExts.contains(fileURL.pathExtension.lowercased()) else { continue }

            if let doc = await extractDocument(from: fileURL) {
                found.append(doc)
            }
        }
        documents = found
        isIndexing = false
        log("RAG: indexed \(found.count) documents from \(url.lastPathComponent)", cat: "rag")
    }

    private func extractDocument(from url: URL) async -> RAGDocument? {
        let modDate = (try? url.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .now
        let content: String

        if url.pathExtension.lowercased() == "pdf" {
            guard let pdfDoc = PDFDocument(url: url), let text = pdfDoc.string, !text.isEmpty else { return nil }
            content = text
        } else {
            guard let text = try? String(contentsOf: url, encoding: .utf8), !text.isEmpty else { return nil }
            content = text
        }

        var doc = RAGDocument(url: url, content: String(content.prefix(50_000)), modifiedAt: modDate)
        doc.chunks = chunk(content)
        return doc
    }

    private func chunk(_ text: String) -> [String] {
        var result: [String] = []
        var idx = text.startIndex
        while idx < text.endIndex {
            let end = text.index(idx, offsetBy: chunkSize, limitedBy: text.endIndex) ?? text.endIndex
            result.append(String(text[idx..<end]))
            idx = end
        }
        return result
    }

    // MARK: Query-time retrieval (keyword TF-IDF style)

    func relevantContext(for query: String, topK: Int = 3) -> String {
        guard !documents.isEmpty else { return "" }

        let queryTerms = query.lowercased()
            .components(separatedBy: .whitespacesAndNewlines)
            .filter { $0.count > 3 }
        guard !queryTerms.isEmpty else { return "" }

        // Score each chunk by term frequency
        var scored: [(String, Double)] = []
        for doc in documents {
            for chunk in doc.chunks {
                let lower = chunk.lowercased()
                let score = Double(queryTerms.filter { lower.contains($0) }.count) / Double(queryTerms.count)
                if score > 0 { scored.append(("[\(doc.title)] \(chunk)", score)) }
            }
        }

        let top = scored.sorted { $0.1 > $1.1 }.prefix(topK).map(\.0)
        guard !top.isEmpty else { return "" }
        return "\n\n--- Local Context ---\n" + top.joined(separator: "\n\n") + "\n---\n"
    }

    // MARK: FSEvents watch

    private func restartWatch() {
        stopWatch()
        guard let url = watchedFolderURL else { return }
        Task { await indexFolder(url) }

        var ctx = FSEventStreamContext(
            version: 0,
            info: Unmanaged.passUnretained(self).toOpaque(),
            retain: nil, release: nil, copyDescription: nil
        )
        let paths = [url.path] as CFArray
        eventStream = FSEventStreamCreate(
            kCFAllocatorDefault, { _, info, _, _, _, _ in
                guard let info else { return }
                let watcher = Unmanaged<RAGWatcher>.fromOpaque(info).takeUnretainedValue()
                Task { @MainActor in
                    if let url = watcher.watchedFolderURL { await watcher.indexFolder(url) }
                }
            },
            &ctx, paths, FSEventStreamEventId(kFSEventStreamEventIdSinceNow), 5.0,
            FSEventStreamCreateFlags(kFSEventStreamCreateFlagUseCFTypes | kFSEventStreamCreateFlagFileEvents)
        )
        if let stream = eventStream {
            FSEventStreamScheduleWithRunLoop(stream, CFRunLoopGetMain(), CFRunLoopMode.defaultMode.rawValue)
            FSEventStreamStart(stream)
        }
    }

    private func stopWatch() {
        guard let stream = eventStream else { return }
        FSEventStreamStop(stream)
        FSEventStreamInvalidate(stream)
        FSEventStreamRelease(stream)
        eventStream = nil
    }
}

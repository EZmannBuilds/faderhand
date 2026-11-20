// Offline-render a MIDI file to a 44.1 kHz WAV with macOS's built-in General MIDI bank (no third-party software).
// Usage: swiftc -O render_midi.swift -o render_midi && ./render_midi in.mid out.wav
// One AVAudioUnitSampler per track (drums on channel 10 use the GM percussion bank). This is a neutral sketch
// render for A/B listening, not a production sound.
import AVFoundation

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: render_midi in.mid out.wav"); exit(2) }
let inURL = URL(fileURLWithPath: args[1]), outURL = URL(fileURLWithPath: args[2])
let dls = URL(fileURLWithPath: "/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls")

let engine = AVAudioEngine()
let format = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 2)!
try engine.enableManualRenderingMode(.offline, format: format, maximumFrameCount: 4096)

let seq = AVAudioSequencer(audioEngine: engine)
try seq.load(from: inURL, options: [])

// read channel and program per track straight from the file
func trackInfo(_ data: Data) -> [(channel: Int, program: Int)] {
    var out: [(Int, Int)] = []
    let b = [UInt8](data); var i = 14
    while i + 8 <= b.count {
        let len = Int(b[i+4]) << 24 | Int(b[i+5]) << 16 | Int(b[i+6]) << 8 | Int(b[i+7])
        var p = i + 8; let end = min(p + len, b.count); var ch = -1; var prog = 0; var running: UInt8 = 0
        while p < end {
            while p < end && b[p] & 0x80 != 0 { p += 1 }; p += 1   // delta time
            if p >= end { break }
            var st = b[p]
            if st == 0xFF { let l = Int(b[p+2]); p += 3 + l; continue }
            if st == 0xF0 || st == 0xF7 { var q = p + 1; var l = 0; while b[q] & 0x80 != 0 { l = (l << 7) | Int(b[q] & 0x7F); q += 1 }; l = (l << 7) | Int(b[q]); p = q + 1 + l; continue }
            if st & 0x80 != 0 { running = st; p += 1 } else { st = running }
            let kind = st & 0xF0
            if ch < 0 && (kind == 0x90 || kind == 0xC0) { ch = Int(st & 0x0F) }
            if kind == 0xC0 { prog = Int(b[p]); p += 1 } else if kind == 0xD0 { p += 1 } else { p += 2 }
        }
        out.append((ch, prog)); i = end
    }
    return out
}
let info = trackInfo(try Data(contentsOf: inURL))
for (n, track) in seq.tracks.enumerated() {
    let s = AVAudioUnitSampler()
    engine.attach(s); engine.connect(s, to: engine.mainMixerNode, format: nil)
    let (ch, prog) = n < info.count ? info[n] : (0, 0)
    if ch == 9 {
        try s.loadSoundBankInstrument(at: dls, program: 0, bankMSB: UInt8(kAUSampler_DefaultPercussionBankMSB), bankLSB: 0)
    } else {
        try s.loadSoundBankInstrument(at: dls, program: UInt8(max(0, prog)), bankMSB: UInt8(kAUSampler_DefaultMelodicBankMSB), bankLSB: 0)
    }
    track.destinationAudioUnit = s
}
engine.mainMixerNode.outputVolume = 0.8
try engine.start()
seq.prepareToPlay(); try seq.start()

let lengthSec = seq.tracks.map { $0.lengthInSeconds }.max() ?? 0
let totalFrames = AVAudioFramePosition((lengthSec + 2.0) * 44100)
var file: AVAudioFile? = try AVAudioFile(forWriting: outURL, settings: format.settings, commonFormat: .pcmFormatFloat32, interleaved: false)
let buf = AVAudioPCMBuffer(pcmFormat: engine.manualRenderingFormat, frameCapacity: engine.manualRenderingMaximumFrameCount)!
while engine.manualRenderingSampleTime < totalFrames {
    let n = min(AVAudioFrameCount(totalFrames - engine.manualRenderingSampleTime), buf.frameCapacity)
    let st = try engine.renderOffline(n, to: buf)
    if st == .success { try file!.write(from: buf) } else if st == .error { print("render error"); exit(1) }
}
seq.stop(); engine.stop()
file = nil  // closes and finalises the WAV
print("wrote \(outURL.path) (\(String(format: "%.1f", lengthSec)) s)")

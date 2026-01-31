
import React, { useState } from 'react';
import { Copy, Check, FileCode, Package, Cpu } from 'lucide-react';

const FILES = [
    {
        id: 'cargo',
        name: 'Cargo.toml',
        icon: Package,
        language: 'toml',
        content: `[package]
name = "serb_stem"
version = "0.1.0"
edition = "2021"
authors = ["Antigravity & USER"]
description = "Fast Serbian stemmer compiled to WebAssembly"

[lib]
name = "serb_stem"
crate-type = ["cdylib", "rlib"]

[dependencies]
wasm-bindgen = "0.2"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[features]
default = []
python = ["dep:pyo3"]

[dependencies.pyo3]
version = "0.19.0"
features = ["extension-module"]
optional = true

[profile.release]
opt-level = "z"
lto = true
codegen-units = 1
panic = "abort"
strip = true`
    },
    {
        id: 'lib_rs',
        name: 'src/lib.rs',
        icon: FileCode,
        language: 'rust',
        content: `pub mod transliteration;
pub mod normalization;
pub mod stemmer;
pub mod voice_rules;

pub use transliteration::{cyrillic_to_latin, latin_to_cyrillic};
pub use normalization::{ekavize, normalize_case, remove_punctuation};
pub use stemmer::{stem, conservative_stem};

// --- WebAssembly Bindings ---
#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub fn stem_wasm(word: &str) -> String {
    stem(word)
}`
    }
];

const FileViewer: React.FC = () => {
    const [activeFile, setActiveFile] = useState(FILES[0]);
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(activeFile.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="flex flex-col lg:flex-row gap-6 animate-in slide-in-from-left-4 duration-500">
            <div className="lg:w-64 space-y-1">
                {FILES.map(file => (
                    <button
                        key={file.id}
                        onClick={() => setActiveFile(file)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 text-sm rounded-xl transition-all ${activeFile.id === file.id ? 'bg-[#21262d] text-[#58a6ff] border border-[#30363d] shadow-lg' : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#161b22]'}`}
                    >
                        <file.icon className="w-4 h-4" />
                        <span className="font-medium">{file.name}</span>
                    </button>
                ))}

                <div className="mt-8 p-4 bg-[#238636]/10 border border-[#238636]/20 rounded-xl">
                    <div className="flex items-center space-x-2 text-[#3fb950] mb-2 font-bold text-xs uppercase tracking-wider">
                        <Cpu className="w-3 h-3" />
                        <span>WASM Ready</span>
                    </div>
                    <p className="text-[10px] text-[#8b949e] leading-relaxed">
                        Kopiraj ove datoteke u svoj projekt i pokreni <code>wasm-pack build</code> za generiranje JS paketa.
                    </p>
                </div>
            </div>

            <div className="flex-grow bg-[#161b22] border border-[#30363d] rounded-2xl overflow-hidden flex flex-col min-h-[500px] shadow-2xl">
                <div className="px-6 py-3 bg-[#0d1117] border-b border-[#30363d] flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-[#ff5f56]"></div>
                        <div className="w-3 h-3 rounded-full bg-[#ffbd2e]"></div>
                        <div className="w-3 h-3 rounded-full bg-[#27c93f]"></div>
                        <span className="ml-4 text-xs text-[#8b949e] font-mono">{activeFile.name}</span>
                    </div>
                    <button
                        onClick={handleCopy}
                        className="p-1.5 hover:bg-[#30363d] rounded-lg transition-colors text-[#8b949e] hover:text-[#f0f6fc] flex items-center space-x-2"
                    >
                        {copied ? <Check className="w-4 h-4 text-[#3fb950]" /> : <Copy className="w-4 h-4" />}
                        <span className="text-[10px] uppercase font-extrabold">{copied ? 'Kopirano!' : 'Copy Source'}</span>
                    </button>
                </div>
                <div className="p-6 flex-grow overflow-auto bg-[#0d1117]">
                    <pre className="font-mono text-sm leading-relaxed whitespace-pre text-[#c9d1d9]">
                        {activeFile.content}
                    </pre>
                </div>
            </div>
        </div>
    );
};

export default FileViewer;

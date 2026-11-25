import * as monaco from "monaco-editor";
import EditorWorker from "../node_modules/monaco-editor/esm/vs/editor/editor.worker.js?worker";

globalThis.MonacoEnvironment = {
    getWorker() {
        return new EditorWorker();
    }
};

let editor;

const defaultCode = {
    cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    cout << "Hello, MultiCode!" << endl;
    return 0;
}`,

    c: `#include <stdio.h>

int main() {
    printf("Hello, MultiCode!\\n");
    return 0;
}`,

    python: `name = input("Enter your name: ")
print("Hello,", name)`,

    java: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, MultiCode!");
    }
}`,

    javascript: `console.log("Hello, MultiCode!");`
};

const languageMap = {
    cpp: "cpp",
    c: "c",
    python: "python",
    java: "java",
    javascript: "javascript"
};

export function createEditor() {
    const container = document.getElementById("editor");

    editor = monaco.editor.create(container, {
        value: defaultCode.cpp,
        language: "cpp",
        theme: "vs-dark",
        automaticLayout: true,

        minimap: {
            enabled: false
        },

        fontSize: 14,
        wordWrap: "on",
        scrollBeyondLastLine: false,
        lineNumbers: "on",
        roundedSelection: true,
        cursorBlinking: "smooth",

        padding: {
            top: 15
        }
    });

    return editor;
}

export function getEditor() {
    return editor;
}

export function changeLanguage(language) {
    if (!editor || !editor.getModel()) return;

    const model = editor.getModel();

    monaco.editor.setModelLanguage(
        model,
        languageMap[language] || "plaintext"
    );

    editor.setValue(defaultCode[language] || "");
}

export function resetEditor(language) {
    if (!editor) return;

    editor.setValue(defaultCode[language] || "");
}

export function toggleTheme() {
    if (!editor) return;

    const currentTheme = editor._themeService
        ? editor._themeService.getColorTheme().themeName
        : "vs-dark";

    const newTheme = currentTheme === "vs-dark" ? "vs" : "vs-dark";

    monaco.editor.setTheme(newTheme);

    return newTheme;
}
import { StreamLanguage } from "@codemirror/language";
import { EditorView, basicSetup } from "codemirror"
import { EditorState } from "@codemirror/state"


const yara = StreamLanguage.define({
  startState() {
    return { inComment: false };
  },
  token(stream, state) {
    if (state.inComment) {
      if (stream.skipTo("*/")) {
        stream.next(); stream.next();
        state.inComment = false;
      } else {
        stream.skipToEnd();
      }
      return "comment";
    }

    if (stream.match(/\/\*/)) {
      state.inComment = true;
      return "comment";
    }

    if (stream.match(/\/\/.*/)) {
      return "comment";
    }

    if (stream.match(/"(?:[^\\]|\\.)*?(?:"|$)/)) {
      return "string";
    }

    if (stream.match(/\b(?:all|and|any|ascii|at|base64|base64wide|condition|contains|entrypoint|filesize|for|fullword|global|import|in|include|int8|int16|int32|int8be|int16be|int32be|matches|meta|nocase|not|or|of|private|rule|strings|them|uint8|uint16|uint32|uint8be|uint16be|uint32be|wide|xor)\b/)) {
      return "keyword";
    }

    if (stream.match(/\b(?:true|false)\b/)) {
      return "atom";
    }

    if (stream.match(/0x[a-f\d]+|(?:\.\d+|\d+\.?\d*)/i)) {
      return "number";
    }

    if (stream.match(/(\{(?:[\s])*(?:[a-fA-F\d?]{2}\s?)+(?:[\s])*\})/)) {
      return "number";
    }

    if (stream.match(/[-+/*=<>:]+/)) {
      return "operator";
    }

    if (stream.match(/\{/)) {
      return "bracket";
    }

    if (stream.match(/\}/)) {
      return "bracket";
    }

    if (stream.match(/\$\w*/)) {
      // return "variableName";
      return "labelName"; // Using because of the difficulty to style variableName
    }

    stream.next();
    return null;
  },

  languageData: {
    commentTokens: { line: "//", block: { open: "/*", close: "*/" } }
  }
});


const fixedHeightEditor = EditorView.theme({
  "&": { height: "300px" },
  ".cm-scroller": { overflow: "auto" },
})

function createYaraEditor(textarea, options={}) {
  const parent = document.createElement('div')
  textarea.parentNode.appendChild(parent)
  textarea.style.display = 'none';
  let content = textarea.value

  if (options.placeholder && content.length == 0) {
    content = options.placeholder
  }

  let updateListener = false
  if (!options.textarea_no_sync || options.textarea_no_sync !== false) {
    updateListener = EditorView.updateListener.of(function (e) {
      if (e.docChanged) {
        textarea.value = e.state.doc.toString();
      }
    })
  }

  const extensionList = [
    basicSetup,
    updateListener || [],
    fixedHeightEditor,
    yara,
    ...(options.codemirror_extensions || [])  // Allow users to pass extra extensions
  ]

  const state = EditorState.create({
    doc: content,
    extensions: extensionList,
  })

  const view = new EditorView({
    state,
    parent
  })

  if (!options.textarea_no_sync || options.textarea_no_sync !== false) {
  }

  return view
}

export { createYaraEditor }

'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

interface RichTextEditorProps {
  content: string
  onChange: (content: string) => void
  placeholder?: string
}

export default function RichTextEditor({ content, onChange, placeholder }: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: placeholder || 'Enter your content here...',
      }),
    ],
    content: content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose focus:outline-none max-w-none'
      }
    },
    immediatelyRender: false // Add this to fix SSR hydration issues
  })

  return (
    <div className="rich-text-editor">
      <div className="menu-bar">
        <button
          onClick={() => editor?.chain().focus().toggleBold().run()}
          className={`menu-item ${editor?.isActive('bold') ? 'is-active' : ''}`}
          title="Bold"
        >
          B
        </button>
        <button
          onClick={() => editor?.chain().focus().toggleItalic().run()}
          className={`menu-item ${editor?.isActive('italic') ? 'is-active' : ''}`}
          title="Italic"
        >
          I
        </button>
        <button
          onClick={() => editor?.chain().focus().toggleBulletList().run()}
          className={`menu-item ${editor?.isActive('bulletList') ? 'is-active' : ''}`}
          title="Bullet List"
        >
          •
        </button>
      </div>
      <EditorContent editor={editor} />
      <style jsx>{`
        .rich-text-editor {
          position: relative;
          background: white;
          border-radius: 0.375rem;
        }
        .menu-bar {
          padding: 0.5rem;
          border-bottom: 1px solid #e5e7eb;
          display: flex;
          gap: 0.5rem;
        }
        .menu-item {
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.375rem;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
        }
        .menu-item:hover {
          background: #f3f4f6;
        }
        .menu-item.is-active {
          background: #eff6ff;
          border-color: #93c5fd;
          color: #2563eb;
        }
        :global(.ProseMirror) {
          padding: 1rem;
          min-height: 120px;
          outline: none;
        }
        :global(.ProseMirror p.is-editor-empty:first-child::before) {
          color: #9ca3af;
          content: attr(data-placeholder);
          float: left;
          height: 0;
          pointer-events: none;
        }
      `}</style>
    </div>
  )
}
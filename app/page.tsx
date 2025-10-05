'use client'

import type { Note } from '@/lib/supabase'
import { supabase } from '@/lib/supabase'
import {
    CalendarIcon,
    CheckCircleIcon,
    ClockIcon,
    DocumentTextIcon,
    PencilSquareIcon,
    PlusIcon,
    TrashIcon,
    XCircleIcon,
} from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import dynamic from 'next/dynamic'

const RichTextEditor = dynamic(() => import('./components/RichTextEditor'), {
  ssr: false // This ensures the component only renders on the client side
})

export default function Home() {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [notes, setNotes] = useState<Note[]>([])
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeView, setActiveView] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredNotes, setFilteredNotes] = useState<Note[]>([])

  useEffect(() => {
    fetchNotes()
  }, [])

  useEffect(() => {
    if (activeView === 'recent') {
      // Filter notes from the last 24 hours
      const recentNotes = notes.filter(note => {
        const createdDate = new Date(note.created_at)
        const now = new Date()
        const timeDiff = now.getTime() - createdDate.getTime()
        const hoursDiff = timeDiff / (1000 * 60 * 60)
        return hoursDiff <= 24
      })
      setFilteredNotes(recentNotes)
    } else if (activeView === 'search' && searchQuery) {
      // Filter notes based on search query
      const searchResults = notes.filter(note =>
        note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        note.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredNotes(searchResults)
    } else {
      setFilteredNotes(notes)
    }
  }, [activeView, notes, searchQuery])

  const fetchNotes = async () => {
    setIsLoading(true)
    const { data, error } = await supabase
      .from('notes')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching notes:', error)
      return
    }

    if (data) {
      setNotes(data)
    }
    setIsLoading(false)
  }

  const createNote = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    const { data, error } = await supabase
      .from('notes')
      .insert([
        {
          title,
          content,
        },
      ])
      .select()

    if (error) {
      console.error('Error creating note:', error)
      return
    }

    if (data) {
      setNotes([...data, ...notes])
      setTitle('')
      setContent('')
    }
    setIsLoading(false)
  }

  const updateNote = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingNote) return

    setIsLoading(true)
    const { error } = await supabase
      .from('notes')
      .update({
        title,
        content,
        updated_at: new Date().toISOString(),
      })
      .eq('id', editingNote.id)

    if (error) {
      console.error('Error updating note:', error)
      return
    }

    setNotes(
      notes.map((note) =>
        note.id === editingNote.id
          ? { ...note, title, content, updated_at: new Date().toISOString() }
          : note
      )
    )

    setEditingNote(null)
    setTitle('')
    setContent('')
    setIsLoading(false)
  }

  const deleteNote = async (id: string) => {
    if (!confirm('Are you sure you want to delete this note?')) return

    setIsLoading(true)
    const { error } = await supabase.from('notes').delete().eq('id', id)

    if (error) {
      console.error('Error deleting note:', error)
      return
    }

    setNotes(notes.filter((note) => note.id !== id))
    setIsLoading(false)
  }

  const startEditing = (note: Note) => {
    setEditingNote(note)
    setTitle(note.title)
    setContent(note.content)
  }

  const cancelEditing = () => {
    setEditingNote(null)
    setTitle('')
    setContent('')
  }

  const getViewTitle = () => {
    switch (activeView) {
      case 'all': return 'All Notes'
      case 'recent': return 'Recent Notes'
      case 'search': return 'Search Results'
      case 'new': return 'Create New Note'
      default: return 'My Notes'
    }
  }

  const getViewDescription = () => {
    switch (activeView) {
      case 'all': return 'Organize your thoughts and ideas'
      case 'recent': return 'Your most recently created notes'
      case 'search': return 'Found notes matching your search'
      case 'new': return 'Create a new note to capture your thoughts'
      default: return 'Organize your thoughts and ideas'
    }
  }

  const handleViewChange = (view: string) => {
    console.log('View changed to:', view) // Debug log
    setActiveView(view)
    // Handle different view actions
    if (view === 'new') {
      // Focus on the form when "New Note" is clicked
      setTimeout(() => {
        document.getElementById('title')?.focus()
      }, 100)
    }
    // Add more view handling logic here as needed
  }

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Sidebar activeView={activeView} onViewChange={handleViewChange} />
      
      <main className="flex-1 lg:ml-0 w-full">
        <div className="max-w-5xl mx-auto p-6 lg:p-8">
          {/* Header */}
          <header className="mb-8 pt-16 lg:pt-0">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5 text-blue-600" />
                  {getViewTitle()}
                  <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full font-normal">
                    {activeView}
                  </span>
                </h1>
                <p className="text-sm text-gray-600 mt-1">{getViewDescription()}</p>
              </div>
              <div className="flex gap-2 items-center">
                {editingNote ? (
                  <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-100 text-blue-800 border border-blue-200">
                    <PencilSquareIcon className="w-3 h-3 mr-1.5" />
                    Editing Note
                  </span>
                ) : (
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search notes..."
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value)
                        setActiveView(e.target.value ? 'search' : 'all')
                      }}
                      className="input-field w-64 pl-8"
                    />
                    <svg
                      className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Form - Only show when not in search or recent view */}
          {(activeView === 'all' || activeView === 'new' || editingNote) && (
            <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-gray-200/50 p-6 mb-8">
              <form onSubmit={editingNote ? updateNote : createNote}>
                <div className="space-y-5">
                  <div>
                    <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                      <PencilSquareIcon className="w-3 h-3" />
                      Title
                    </label>
                    <input
                      id="title"
                      type="text"
                      placeholder="Enter note title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                      <DocumentTextIcon className="w-3 h-3" />
                      Content
                    </label>
                    <div className="input-field min-h-[120px] prose max-w-none">
                      <RichTextEditor
                        content={content}
                        onChange={setContent}
                        placeholder="Enter note content"
                      />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="submit"
                      className="btn-primary flex-1 sm:flex-none justify-center"
                      disabled={isLoading}
                    >
                      {editingNote ? (
                        <>
                          <CheckCircleIcon className="w-4 h-4" />
                          Update Note
                        </>
                      ) : (
                        <>
                          <PlusIcon className="w-4 h-4" />
                          Create Note
                        </>
                      )}
                    </button>
                    {editingNote && (
                      <button
                        type="button"
                        onClick={cancelEditing}
                        className="btn-secondary flex-1 sm:flex-none justify-center"
                      >
                        <XCircleIcon className="w-4 h-4" />
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </form>
            </div>
          )}

          {/* Notes Grid - Hide when in new note view */}
          {activeView !== 'new' && (isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="text-sm text-gray-500 mt-3">Loading notes...</p>
            </div>
          ) : filteredNotes.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <DocumentTextIcon className="w-5 h-5 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No notes yet</h3>
              <p className="text-sm text-gray-500">Get started by creating your first note</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredNotes.map((note, index) => (
                <div 
                  key={note.id} 
                  className="bg-white/90 backdrop-blur-sm rounded-xl shadow-sm border border-gray-200/50 p-5 hover:shadow-md transition-all duration-200 hover:border-blue-200/50 group relative"
                  style={{
                    animationDelay: `${index * 0.1}s`,
                    animation: 'fadeInUp 0.5s ease-out forwards',
                  }}
                >
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-200">
                    <div className="flex gap-1">
                      <button
                        onClick={() => startEditing(note)}
                        className="p-1.5 rounded-md transition-colors hover:bg-blue-50 text-blue-600"
                        title="Edit note"
                      >
                        <PencilSquareIcon className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => deleteNote(note.id)}
                        className="p-1.5 rounded-md transition-colors hover:bg-red-50 text-red-600"
                        title="Delete note"
                      >
                        <TrashIcon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <h2 className="text-lg font-semibold mb-3 text-gray-800 pr-16 line-clamp-1">{note.title}</h2>
                  <p className="text-gray-600 mb-4 whitespace-pre-wrap line-clamp-3 text-sm leading-relaxed">{note.content}</p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500 pt-3 border-t border-gray-100">
                    <span className="inline-flex items-center gap-1.5" title="Created date">
                      <CalendarIcon className="w-3 h-3 text-blue-500/70" />
                      {new Date(note.created_at).toLocaleDateString()}
                    </span>
                    <span className="inline-flex items-center gap-1.5" title="Last updated">
                      <ClockIcon className="w-3 h-3 text-green-500/70" />
                      {new Date(note.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
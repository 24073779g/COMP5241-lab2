'use client'

import {
  Bars3Icon,
  DocumentTextIcon,
  HomeIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { useState } from 'react'

interface SidebarProps {
  activeView: string
  onViewChange: (view: string) => void
}

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false)

  const menuItems = [
    { id: 'all', label: 'All Notes', icon: HomeIcon, count: null },
    { id: 'recent', label: 'Recent', icon: DocumentTextIcon, count: null },
  ]

  const toggleSidebar = () => setIsOpen(!isOpen)

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white/90 backdrop-blur-sm shadow-md border border-gray-200"
      >
        {isOpen ? (
          <XMarkIcon className="w-5 h-5 text-gray-600" />
        ) : (
          <Bars3Icon className="w-5 h-5 text-gray-600" />
        )}
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/20 backdrop-blur-sm z-30"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:sticky top-0 left-0 h-screen w-72 bg-white/95 backdrop-blur-md
          border-r border-gray-200/50 shadow-lg lg:shadow-none z-40
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-gray-200/50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-lg font-semibold text-gray-800">NotesApp</h1>
            </div>
          </div>



           {/* Quick Action */}
           <div className="p-4 border-b border-gray-200/50">
             <button
               onClick={() => {
                 console.log('New Note clicked') // Debug log
                 onViewChange('new')
               }}
               className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md ${
                 activeView === 'new'
                   ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                   : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700'
               }`}
             >
               <PlusIcon className="w-4 h-4" />
               <span className="text-sm font-medium">New Note</span>
             </button>
           </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <ul className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = activeView === item.id
                
                return (
                  <li key={item.id}>
                     <button
                       onClick={() => {
                         console.log('Menu item clicked:', item.id) // Debug log
                         onViewChange(item.id)
                         setIsOpen(false) // Close mobile menu
                       }}
                       className={`
                         w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left
                         transition-all duration-200 group
                         ${isActive
                           ? 'bg-blue-50 text-blue-700 border border-blue-200/50 shadow-sm'
                           : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                         }
                       `}
                     >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-gray-500 group-hover:text-gray-600'}`} />
                      <span className="text-sm font-medium">{item.label}</span>
                      {item.count && (
                        <span className="ml-auto text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded-full">
                          {item.count}
                        </span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          </nav>


        </div>
      </aside>
    </>
  )
}

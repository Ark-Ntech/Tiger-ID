import { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon, WrenchScrewdriverIcon } from '@heroicons/react/24/outline'
import Button from '../common/Button'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useGetMCPToolsQuery } from '../../app/api'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  agent_type?: string
}

interface ChatInterfaceProps {
  investigationId: string
}

const ChatInterface = ({ investigationId }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set())
  const [showToolSelector, setShowToolSelector] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { data: mcpToolsData, isLoading: toolsLoading } = useGetMCPToolsQuery()
  
  const mcpServers = mcpToolsData?.data?.servers || {}
  const allTools: Array<{ name: string; description: string; server?: string }> = []
  Object.values(mcpServers).forEach((server: any) => {
    if (server.tools) {
      server.tools.forEach((tool: any) => {
        allTools.push({ ...tool, server: server.name })
      })
    }
  })

  const { send, isConnected } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'chat_message') {
        setMessages((prev) => [...prev, message.data])
        setIsTyping(false)
      } else if (message.type === 'agent_update') {
        setIsTyping(message.data.status === 'working')
      }
    },
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !isConnected) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    
    send({
      type: 'chat_message',
      investigation_id: investigationId,
      content: input,
      selected_tools: selectedTools.size > 0 ? Array.from(selectedTools) : undefined,
    })

    setInput('')
    setIsTyping(true)
  }

  const toggleTool = (toolName: string) => {
    setSelectedTools(prev => {
      const next = new Set(prev)
      if (next.has(toolName)) {
        next.delete(toolName)
      } else {
        next.add(toolName)
      }
      return next
    })
  }

  return (
    <Card className="h-full flex flex-col">
      <div className="border-b pb-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">AI Assistant</h3>
            <p className="text-sm text-gray-500">
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowToolSelector(!showToolSelector)}
          >
            <WrenchScrewdriverIcon className="h-4 w-4 mr-1" />
            Tools ({selectedTools.size})
          </Button>
        </div>
        
        {showToolSelector && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Available Tools</h4>
            {toolsLoading ? (
              <p className="text-sm text-gray-500">Loading tools...</p>
            ) : allTools.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {allTools.map((tool) => (
                  <label
                    key={`${tool.server}-${tool.name}`}
                    className="flex items-start space-x-2 p-2 hover:bg-gray-100 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedTools.has(tool.name)}
                      onChange={() => toggleTool(tool.name)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">{tool.name}</span>
                        {tool.server && (
                          <Badge variant="info" className="text-xs">
                            {tool.server}
                          </Badge>
                        )}
                      </div>
                      {tool.description && (
                        <p className="text-xs text-gray-600 mt-1">{tool.description}</p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No tools available</p>
            )}
          </div>
        )}
        
        {selectedTools.size > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {Array.from(selectedTools).map((toolName) => (
              <Badge key={toolName} variant="info" className="text-xs">
                {toolName}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <p>Start a conversation with the AI assistant</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : message.role === 'system'
                  ? 'bg-gray-100 text-gray-800'
                  : 'bg-blue-100 text-blue-900'
              }`}
            >
              {message.agent_type && (
                <p className="text-xs opacity-75 mb-1">
                  {message.agent_type} Agent
                </p>
              )}
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          disabled={!isConnected}
        />
        <Button
          type="submit"
          variant="primary"
          disabled={!input.trim() || !isConnected}
        >
          <PaperAirplaneIcon className="h-5 w-5" />
        </Button>
      </form>
    </Card>
  )
}

export default ChatInterface


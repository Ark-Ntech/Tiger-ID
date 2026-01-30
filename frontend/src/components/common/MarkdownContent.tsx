import ReactMarkdown from 'react-markdown'
import { cn } from '../../utils/cn'

interface MarkdownContentProps {
  content: string
  className?: string
}

export const MarkdownContent: React.FC<MarkdownContentProps> = ({ content, className }) => {
  return (
    <ReactMarkdown
      className={cn('prose prose-gray max-w-none', className)}
      components={{
        h1: ({children}) => <h1 className="text-2xl font-bold text-gray-900 mb-4">{children}</h1>,
        h2: ({children}) => <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">{children}</h2>,
        h3: ({children}) => <h3 className="text-lg font-medium text-gray-700 mt-4 mb-2">{children}</h3>,
        strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
        ul: ({children}) => <ul className="list-disc ml-5 space-y-1 my-2">{children}</ul>,
        ol: ({children}) => <ol className="list-decimal ml-5 space-y-1 my-2">{children}</ol>,
        li: ({children}) => <li className="text-gray-700">{children}</li>,
        p: ({children}) => <p className="text-gray-700 mb-3">{children}</p>,
        table: ({children}) => <table className="min-w-full border border-gray-200 my-4">{children}</table>,
        th: ({children}) => <th className="border border-gray-200 px-3 py-2 bg-gray-50 font-semibold">{children}</th>,
        td: ({children}) => <td className="border border-gray-200 px-3 py-2">{children}</td>,
        a: ({href, children}) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline"
          >
            {children}
          </a>
        ),
        code: ({children}) => (
          <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">
            {children}
          </code>
        ),
        pre: ({children}) => (
          <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4">
            {children}
          </pre>
        ),
        blockquote: ({children}) => (
          <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
            {children}
          </blockquote>
        ),
        hr: () => <hr className="my-6 border-gray-200" />,
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export default MarkdownContent

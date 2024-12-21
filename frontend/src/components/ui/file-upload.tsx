"use client"

import { ExternalLink, FileIcon, UploadCloud, X } from "lucide-react"
import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Button } from "./button"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card"

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  existingFiles?: Array<{ id: number; file: string; file_type: string; description?: string }>
  onFileRemove?: (fileId: number) => void
}

export function FileUpload({ onFilesSelected, existingFiles = [], onFileRemove }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.filter(
        (file) => !files.some((existingFile) => existingFile.name === file.name)
      )
      setFiles((prev) => [...prev, ...newFiles])
      onFilesSelected(newFiles)
    },
    [onFilesSelected, files]
  )

  const handleRemoveNewFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index)
    setFiles(updatedFiles)
    onFilesSelected(updatedFiles) // Update parent component
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  return (
    <div className="space-y-6">
      {/* Dropzone Area */}
      <Card className="border-dashed">
        <div
          {...getRootProps()}
          className={`p-6 cursor-pointer text-center
            ${isDragActive ? "bg-primary/5" : ""}`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">
            {isDragActive ? "Drop files here" : "Drag & drop files here, or click to select"}
          </p>
        </div>
      </Card>

      {/* Existing Files */}
      {existingFiles.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Existing Files</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {existingFiles.map((file) => (
              <Card key={file.id} className="group hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <FileIcon className="h-4 w-4 text-muted-foreground" />
                      <CardTitle className="text-sm font-medium">{file.file_type}</CardTitle>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link
                        href={file.file}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Link>
                      {onFileRemove && (
                        <Button 
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            onFileRemove(file.id)
                          }}
                          className="h-4 w-4 text-red-600 hover:text-red-800"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                {file.description && (
                  <CardContent>
                    <CardDescription className="text-xs">
                      {file.description}
                    </CardDescription>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* New Files */}
      {files.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium">New Files</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.map((file, index) => (
              <Card key={index} className="group hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <FileIcon className="h-4 w-4 text-muted-foreground" />
                      <CardTitle className="text-sm font-medium">{file.name}</CardTitle>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveNewFile(index)}
                      className="h-4 w-4 text-red-600 hover:text-red-800 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

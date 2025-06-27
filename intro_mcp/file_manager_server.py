#!/usr/bin/env python3
"""
File Manager MCP Server
Cho phép Claude đọc/ghi file trên máy tính
"""

import asyncio
import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Tạo server instance
server = Server("file-manager")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Liệt kê các tools có sẵn"""
    return [
        Tool(
            name="read_file",
            description="Đọc nội dung file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string", 
                        "description": "Đường dẫn đến file cần đọc"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Ghi nội dung vào file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Đường dẫn file cần ghi"
                    },
                    "content": {
                        "type": "string",
                        "description": "Nội dung cần ghi vào file"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_files",
            description="Liệt kê file trong thư mục",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Đường dẫn thư mục (để trống = thư mục hiện tại)",
                        "default": "."
                    }
                }
            }
        ),
        Tool(
            name="get_current_directory",
            description="Xem thư mục hiện tại của server",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Xử lý các tool calls"""
    
    if name == "read_file":
        file_path = arguments["path"]
        try:
            # Hiển thị đường dẫn đầy đủ
            full_path = os.path.abspath(file_path)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return [TextContent(
                type="text",
                text=f"File: {full_path}\n\nNội dung:\n{'-'*50}\n{content}\n{'-'*50}"
            )]
            
        except FileNotFoundError:
            return [TextContent(
                type="text",
                text=f"Không tìm thấy file: {os.path.abspath(file_path)}"
            )]
        except UnicodeDecodeError:
            return [TextContent(
                type="text",
                text=f"Không thể đọc file (có thể là file binary): {os.path.abspath(file_path)}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Lỗi khi đọc file: {str(e)}"
            )]
    
    elif name == "write_file":
        file_path = arguments["path"]
        content = arguments["content"]
        
        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            full_path = os.path.abspath(file_path)
            return [TextContent(
                type="text",
                text=f"Đã ghi file thành công: {full_path}"
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Lỗi khi ghi file: {str(e)}"
            )]
    
    elif name == "list_files":
        directory = arguments.get("directory", ".")
        
        try:
            full_dir_path = os.path.abspath(directory)
            files = os.listdir(directory)
            
            if not files:
                return [TextContent(
                    type="text",
                    text=f"Thư mục trống: {full_dir_path}"
                )]
            
            # Phân loại file và folder
            folders = [f for f in files if os.path.isdir(os.path.join(directory, f))]
            files_only = [f for f in files if os.path.isfile(os.path.join(directory, f))]
            
            result = f"Thư mục: {full_dir_path}\n\n"
            
            if folders:
                result += "Thư mục con:\n"
                for folder in sorted(folders):
                    result += f"  {folder}/\n"
                result += "\n"
            
            if files_only:
                result += "Files:\n"
                for file in sorted(files_only):
                    file_path = os.path.join(directory, file)
                    size = os.path.getsize(file_path)
                    result += f"  {file} ({size} bytes)\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Lỗi khi liệt kê thư mục: {str(e)}"
            )]
    
    elif name == "get_current_directory":
        current_dir = os.getcwd()
        return [TextContent(
            type="text",
            text=f"Thư mục hiện tại của server: {current_dir}"
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Tool không tồn tại: {name}"
        )]

async def main():
    """Main function để chạy server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
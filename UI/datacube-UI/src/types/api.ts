export interface FileMetadata {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  storage_type: 'gridfs';
  uploaded_at: string;
  updated_at: string;
}

export interface FileStorageStats {
  total_files: number;
  total_storage_bytes: number;
}

export interface PaginationInfo {
  current_page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface FileListResponse {
  success: boolean;
  data: FileMetadata[];
  stats: FileStorageStats;
  pagination: PaginationInfo;
}

export interface FileUploadResponse {
  success: boolean;
  file_id: string;
  filename: string;
  file_size: number;
}

export interface FileDetailResponse {
  success: boolean;
  info: {
    filename: string;
    upload_date: string;
    length: number;
    metadata: {
      contentType: string;
      user_id: string;
    };
  };
}

// Date utilities for consistent server-client rendering
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  try {
    // Use consistent UTC formatting to avoid timezone hydration mismatches
    const date = new Date(dateString)
    return date.toISOString().split('T')[0] // YYYY-MM-DD format
  } catch {
    return 'N/A'
  }
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  try {
    // Use consistent UTC formatting to avoid timezone hydration mismatches
    const date = new Date(dateString)
    return date.toISOString().replace('T', ' ').slice(0, 19) + ' UTC'
  } catch {
    return 'N/A'
  }
}

export function getDownloadFilename(format: string): string {
  // Use a static date format to prevent hydration mismatches
  // This could be generated server-side or use a consistent timestamp
  return `renec_data_${new Date().toISOString().split('T')[0]}.${format}`
}
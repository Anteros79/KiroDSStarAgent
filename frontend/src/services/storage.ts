import { Investigation } from '../types/investigation'

const STORAGE_KEY = 'ds-star-investigations'

class StorageService {
  // Get all investigations
  getAll(): Investigation[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      if (!data) return []
      const investigations = JSON.parse(data)
      // Convert date strings back to Date objects
      return investigations.map((inv: any) => ({
        ...inv,
        createdAt: new Date(inv.createdAt),
        updatedAt: new Date(inv.updatedAt),
        steps: inv.steps.map((step: any) => ({
          ...step,
          createdAt: new Date(step.createdAt),
          iterations: step.iterations.map((iter: any) => ({
            ...iter,
            timestamp: new Date(iter.timestamp),
          })),
        })),
      }))
    } catch (e) {
      console.error('Failed to load investigations:', e)
      return []
    }
  }

  // Get single investigation by ID
  get(id: string): Investigation | null {
    const all = this.getAll()
    return all.find(inv => inv.id === id) || null
  }

  // Save investigation
  save(investigation: Investigation): void {
    try {
      const all = this.getAll()
      const index = all.findIndex(inv => inv.id === investigation.id)
      
      if (index >= 0) {
        all[index] = investigation
      } else {
        all.push(investigation)
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(all))
    } catch (e) {
      console.error('Failed to save investigation:', e)
    }
  }

  // Delete investigation
  delete(id: string): void {
    try {
      const all = this.getAll()
      const filtered = all.filter(inv => inv.id !== id)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
    } catch (e) {
      console.error('Failed to delete investigation:', e)
    }
  }

  // Get recent investigations
  getRecent(limit: number = 5): Investigation[] {
    const all = this.getAll()
    return all
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
      .slice(0, limit)
  }
}

export const storageService = new StorageService()

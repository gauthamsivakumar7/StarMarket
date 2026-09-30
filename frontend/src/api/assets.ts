import { apiRequest } from './client'
import type { Asset, AssetDetail } from '../types/asset'

export function listAssets(): Promise<Asset[]> {
  return apiRequest<Asset[]>('/assets')
}

export function getAsset(assetId: string): Promise<AssetDetail> {
  return apiRequest<AssetDetail>(`/assets/${assetId}`)
}

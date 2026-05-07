import axios from 'axios'

const BASE = 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE })

export const uploadFile      = (formData) => api.post('/upload', formData)
export const switchFile      = (filename) => api.post(`/switch?filename=${encodeURIComponent(filename)}`)
export const listFiles       = ()          => api.get('/files')
export const getProfile      = (filename)  => api.get(`/profile${filename ? `?filename=${encodeURIComponent(filename)}` : ''}`)
export const sendChat        = (question)  => api.post('/chat', { question })
export const evalQuery       = (question)  => api.post('/eval/query', { question })
export const getGraph        = ()          => api.get('/graph')
export const summarizeSession= ()          => api.post('/graph/summarize')
export const compareSessions = (a, b)      => api.get(`/graph/compare/${a}/${b}`)
export const listSummaries   = ()          => api.get('/graph/summaries')
export const searchColumns   = (query, top_k=5) => api.post('/search/columns', { query, top_k })
export const preprocessFull  = ()          => api.post('/preprocess/full')
export const evalSession     = ()          => api.get('/eval/session')
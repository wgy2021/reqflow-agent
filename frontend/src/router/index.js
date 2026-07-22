import {
  createRouter,
  createWebHistory,
} from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/requirements',
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () =>
      import('../views/DashboardView.vue'),
  },
  {
    path: '/requirements',
    name: 'requirements',
    component: () =>
      import('../views/RequirementsView.vue'),
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () =>
      import('../views/AnalysisWorkspaceView.vue'),
  },
  {
    path: '/analysis-history',
    name: 'history',
    component: () =>
      import('../views/AnalysisHistoryView.vue'),
  },
  {
  path: '/knowledge',
  name: 'knowledge',
  component: () =>
    import('../views/KnowledgeBaseView.vue'),
  },

  {
    path: '/settings',
    name: 'settings',
    component: () =>
      import('../views/SystemSettingsView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
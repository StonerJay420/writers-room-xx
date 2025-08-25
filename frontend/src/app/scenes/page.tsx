'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ScenesPage() {
  const router = useRouter()
  
  useEffect(() => {
    router.push('/')
  }, [router])
  
  return null
}

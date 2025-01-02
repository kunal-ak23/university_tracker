"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts"
import { getRevenueOverview } from "@/service/api/dashboard"

export function Overview() {
  const [data, setData] = useState<Array<{ name: string; total: number }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await getRevenueOverview(new Date().getFullYear())
        console.log(response);
        setData(response.data)
      } catch (error) {
        console.error('Failed to load revenue overview:', error)
        setError('Failed to load revenue data')
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[350px] items-center justify-center">
        <div className="text-muted-foreground">Loading revenue data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[350px] items-center justify-center">
        <div className="text-destructive">{error}</div>
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="flex h-[350px] items-center justify-center">
        <div className="text-muted-foreground">No revenue data available</div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <XAxis
          dataKey="name"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `₹${value.toLocaleString()}`}
        />
        <Tooltip
          cursor={{ fill: 'transparent' }}
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              return (
                <div className="rounded-lg border bg-background p-2 shadow-sm">
                  <div className="grid grid-cols-2 gap-2">
                    {payload.length > 0 && payload[0] && <div className="flex flex-col">
                      <span className="text-[0.70rem] uppercase text-muted-foreground">
                        Revenue
                      </span>
                      <span className="font-bold text-muted-foreground">
                        ₹{payload[0]?.value?.toLocaleString()}
                      </span>
                    </div>}
                  </div>
                </div>
              )
            }
            return null
          }}
        />
        <Bar
          dataKey="total"
          fill="currentColor"
          radius={[4, 4, 0, 0]}
          className="fill-primary"
        />
      </BarChart>
    </ResponsiveContainer>
  )
} 
import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors', {
  variants: {
    variant: {
      default: 'border border-primary/20 bg-primary/10 text-primary hover:bg-primary/15',
      secondary: 'border border-secondary/20 bg-secondary/10 text-secondary-foreground hover:bg-secondary/15',
      accent: 'border border-accent/20 bg-accent/10 text-accent hover:bg-accent/15',
      destructive: 'border border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/15',
      outline: 'border border-border bg-transparent text-foreground hover:bg-muted',
      success: 'border border-green-500/20 bg-green-500/10 text-green-600 dark:text-green-400 hover:bg-green-500/15',
      warning: 'border border-yellow-500/20 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-500/15',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
})

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }

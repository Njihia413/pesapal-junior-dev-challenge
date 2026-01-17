
import { cva } from 'class-variance-authority';
import { Button } from '@/components/ui/button';

export const interactiveHoverButtonVariants = cva(
  'transition-colors duration-300 ease-in-out',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline:
          'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
        interactive: 'bg-background border border-primary rounded-full hover:bg-primary hover:text-primary-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export const InteractiveHoverButton = ({ className, variant, size, children, ...props }: { className?: string, variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link' | 'interactive', size?: 'default' | 'sm' | 'lg' | 'icon', children?: React.ReactNode, [key: string]: any }) => (
  <Button
    className={interactiveHoverButtonVariants({ variant, size, className })}
    {...props}
  >
    {children}
  </Button>
);

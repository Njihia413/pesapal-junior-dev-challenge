import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface User {
  id: number;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  has_elevated_access?: boolean;
}

interface Store {
  authToken: string | null;
  setAuthToken: (token: string | null) => void;
  user: User | null;
  setUser: (user: User | null) => void;
  hasElevatedAccess: boolean;
  setHasElevatedAccess: (hasAccess: boolean) => void;
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      authToken: null,
      setAuthToken: (token: string | null) => set({ authToken: token }),
      user: null,
      setUser: (user: User | null) => set({ user }),
      hasElevatedAccess: false,
      setHasElevatedAccess: (hasAccess: boolean) => set({ hasElevatedAccess: hasAccess }),
    }),
    {
      name: 'argus-auth-storage', // name of the item in the storage (must be unique)
      storage: createJSONStorage(() => sessionStorage), // (optional) by default, 'localStorage' is used
      partialize: (state) => ({
        authToken: state.authToken,
        user: state.user,
        hasElevatedAccess: state.hasElevatedAccess,
      }),
    }
  )
);
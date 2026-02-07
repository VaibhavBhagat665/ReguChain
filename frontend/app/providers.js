'use client';

import { wagmiConfig, chains, RainbowKitProvider, WagmiConfig, darkTheme } from '../lib/wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export default function Providers({ children }) {
    const [queryClient] = useState(() => new QueryClient());

    return (
        <QueryClientProvider client={queryClient}>
            <WagmiConfig config={wagmiConfig}>
                <RainbowKitProvider
                    chains={chains}
                    theme={darkTheme({
                        accentColor: '#3b82f6',
                        accentColorForeground: 'white',
                        borderRadius: 'medium',
                    })}
                    coolMode
                >
                    {children}
                </RainbowKitProvider>
            </WagmiConfig>
        </QueryClientProvider>
    );
}

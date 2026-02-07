'use client';

import { useState, useEffect } from 'react';

// Lazy initialize RainbowKit only on client side
export default function Providers({ children }) {
    const [mounted, setMounted] = useState(false);
    const [providers, setProviders] = useState(null);

    useEffect(() => {
        // Only initialize wallet on client side
        const initWallet = async () => {
            try {
                const { getDefaultWallets, RainbowKitProvider, darkTheme } = await import('@rainbow-me/rainbowkit');
                const { configureChains, createConfig, WagmiConfig } = await import('wagmi');
                const { mainnet, polygon, bsc, arbitrum, optimism, base, sepolia } = await import('wagmi/chains');
                const { publicProvider } = await import('wagmi/providers/public');
                await import('@rainbow-me/rainbowkit/styles.css');

                const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID;

                if (!projectId) {
                    console.warn('WalletConnect projectId not set. Wallet features will be limited.');
                    setMounted(true);
                    return;
                }

                const { chains, publicClient, webSocketPublicClient } = configureChains(
                    [mainnet, polygon, bsc, arbitrum, optimism, base, sepolia],
                    [publicProvider()]
                );

                const { connectors } = getDefaultWallets({
                    appName: 'ReguChain',
                    projectId,
                    chains
                });

                const wagmiConfig = createConfig({
                    autoConnect: true,
                    connectors,
                    publicClient,
                    webSocketPublicClient
                });

                setProviders({ WagmiConfig, RainbowKitProvider, wagmiConfig, chains, darkTheme });
            } catch (error) {
                console.error('Failed to initialize wallet providers:', error);
            }
            setMounted(true);
        };

        initWallet();
    }, []);

    // Show loading or children without wallet on SSR
    if (!mounted) {
        return <>{children}</>;
    }

    // If providers failed to initialize, just render children
    if (!providers) {
        return <>{children}</>;
    }

    const { WagmiConfig, RainbowKitProvider, wagmiConfig, chains, darkTheme } = providers;

    return (
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
    );
}

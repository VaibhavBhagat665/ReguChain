'use client';

import { getDefaultWallets, RainbowKitProvider, darkTheme } from '@rainbow-me/rainbowkit';
import { configureChains, createConfig, WagmiConfig } from 'wagmi';
import { mainnet, polygon, bsc, arbitrum, optimism, base, sepolia } from 'wagmi/chains';
import { publicProvider } from 'wagmi/providers/public';
import '@rainbow-me/rainbowkit/styles.css';

// Configure chains
const { chains, publicClient, webSocketPublicClient } = configureChains(
    [mainnet, polygon, bsc, arbitrum, optimism, base, sepolia],
    [publicProvider()]
);

// Get default wallets (MetaMask, Coinbase, WalletConnect, etc.)
// NOTE: Get a free project ID from https://cloud.walletconnect.com
const { connectors } = getDefaultWallets({
    appName: 'ReguChain',
    projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || '',
    chains
});

// Create wagmi config
const wagmiConfig = createConfig({
    autoConnect: true,
    connectors,
    publicClient,
    webSocketPublicClient
});

export { wagmiConfig, chains, RainbowKitProvider, WagmiConfig, darkTheme };

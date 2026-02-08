'use client';

import { useState, useEffect } from 'react';

export default function WalletConnect({ onAddressSelect }) {
  const [address, setAddress] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');
  const [chainId, setChainId] = useState(null);

  // Check for existing connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      if (typeof window !== 'undefined' && window.ethereum) {
        try {
          const accounts = await window.ethereum.request({ method: 'eth_accounts' });
          if (accounts && accounts.length > 0) {
            setAddress(accounts[0]);
            onAddressSelect(accounts[0]);

            const chainIdHex = await window.ethereum.request({ method: 'eth_chainId' });
            setChainId(parseInt(chainIdHex, 16));
          }
        } catch (err) {
          console.log('No existing connection');
        }
      }
    };
    checkConnection();
  }, [onAddressSelect]);

  // Listen for account and chain changes
  useEffect(() => {
    if (typeof window !== 'undefined' && window.ethereum) {
      const handleAccountsChanged = (accounts) => {
        if (accounts.length > 0) {
          setAddress(accounts[0]);
          onAddressSelect(accounts[0]);
        } else {
          setAddress('');
          onAddressSelect('');
        }
      };

      const handleChainChanged = (chainIdHex) => {
        setChainId(parseInt(chainIdHex, 16));
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, [onAddressSelect]);

  const connectWallet = async () => {
    setError('');
    setIsConnecting(true);

    try {
      if (typeof window === 'undefined' || !window.ethereum) {
        setError('Please install MetaMask or another Web3 wallet');
        return;
      }

      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      });

      if (accounts && accounts.length > 0) {
        setAddress(accounts[0]);
        onAddressSelect(accounts[0]);

        const chainIdHex = await window.ethereum.request({ method: 'eth_chainId' });
        setChainId(parseInt(chainIdHex, 16));
      }
    } catch (err) {
      if (err.code === 4001) {
        setError('Connection rejected by user');
      } else {
        setError(err.message || 'Failed to connect');
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setAddress('');
    setChainId(null);
    onAddressSelect('');
  };

  const getChainName = (id) => {
    const chains = {
      1: 'Ethereum',
      137: 'Polygon',
      56: 'BSC',
      42161: 'Arbitrum',
      10: 'Optimism',
      8453: 'Base',
      11155111: 'Sepolia'
    };
    return chains[id] || `Chain ${id}`;
  };

  if (address) {
    return (
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
        <div className="flex items-center justify-between mb-3">
          {chainId && (
            <span className="px-3 py-1 bg-white dark:bg-slate-800 rounded-lg text-sm font-medium border border-slate-200 dark:border-slate-700">
              {getChainName(chainId)}
            </span>
          )}
          <span className="flex items-center gap-1.5 text-green-600 text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            Connected
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
              {address.substring(2, 4).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {address.substring(0, 6)}...{address.substring(38)}
              </p>
              <p className="text-xs text-slate-500">Wallet Connected</p>
            </div>
          </div>
          <button
            onClick={disconnectWallet}
            className="px-3 py-1.5 text-xs font-medium text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          >
            Disconnect
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <button
        onClick={connectWallet}
        disabled={isConnecting}
        className="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white py-4 px-6 rounded-xl hover:from-blue-700 hover:to-cyan-600 transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transform hover:scale-[1.02] font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
      >
        {isConnecting ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Connecting...
          </>
        ) : (
          <>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Connect Wallet
          </>
        )}
      </button>
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400 text-center">{error}</p>
        </div>
      )}
      <p className="text-xs text-slate-500 text-center">
        Supports MetaMask, Coinbase Wallet, and other browser wallets
      </p>
    </div>
  );
}

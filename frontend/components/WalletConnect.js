'use client';

import { useState, useEffect } from 'react';
import { Wallet, Link2, AlertCircle, CheckCircle, Copy, Shield, Activity, ExternalLink } from 'lucide-react';
import { ethers } from 'ethers';

export default function WalletConnect({ onAddressSelect }) {
  const [address, setAddress] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [balance, setBalance] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [ensName, setEnsName] = useState(null);
  const [walletType, setWalletType] = useState('');

  // Check if wallet is already connected
  useEffect(() => {
    checkConnection();
    
    // Listen for account changes
    if (typeof window.ethereum !== 'undefined') {
      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', () => window.location.reload());
    }
    
    return () => {
      if (typeof window.ethereum !== 'undefined') {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
      }
    };
  }, []);

  const handleAccountsChanged = (accounts) => {
    if (accounts.length === 0) {
      // User disconnected wallet
      setAddress('');
      onAddressSelect('');
    } else {
      // User switched accounts
      setAddress(accounts[0]);
      onAddressSelect(accounts[0]);
    }
  };

  const checkConnection = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ 
          method: 'eth_accounts' 
        });
        if (accounts.length > 0) {
          setAddress(accounts[0]);
          onAddressSelect(accounts[0]);
        }
      } catch (err) {
        console.error('Error checking connection:', err);
      }
    }
  };

  const connectWallet = async () => {
    setError('');
    setIsConnecting(true);

    try {
      // Check if any Web3 wallet is available
      if (typeof window.ethereum === 'undefined') {
        setError('Please install MetaMask, Coinbase Wallet, or another Web3 wallet');
        setIsConnecting(false);
        return;
      }

      console.log('Attempting to connect wallet...');
      
      // Request account access
      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });
      
      console.log('Accounts received:', accounts);
      
      if (accounts && accounts.length > 0) {
        const connectedAddress = accounts[0];
        console.log('Connected address:', connectedAddress);
        
        setAddress(connectedAddress);
        
        // Create provider and get additional wallet info
        try {
          const provider = new ethers.BrowserProvider(window.ethereum);
          await getWalletInfo(provider, connectedAddress);
        } catch (providerError) {
          console.warn('Could not get wallet info:', providerError);
          // Continue anyway, basic connection is working
        }
        
        // Detect wallet type
        if (window.ethereum.isMetaMask) {
          setWalletType('MetaMask');
        } else if (window.ethereum.isCoinbaseWallet) {
          setWalletType('Coinbase Wallet');
        } else {
          setWalletType('Web3 Wallet');
        }
        
        // Notify parent component
        onAddressSelect(connectedAddress);
        console.log('Wallet connected successfully');
      } else {
        setError('No accounts found. Please unlock your wallet.');
      }
    } catch (err) {
      console.error('Error connecting wallet:', err);
      
      if (err.code === 4001) {
        setError('Connection rejected by user');
      } else if (err.code === -32002) {
        setError('Please open your wallet and accept the connection');
      } else {
        setError('Failed to connect wallet: ' + (err.message || 'Unknown error'));
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const getWalletInfo = async (provider, walletAddress) => {
    try {
      // Get balance
      const balanceWei = await provider.getBalance(walletAddress);
      const balanceEth = ethers.formatEther(balanceWei);
      setBalance(parseFloat(balanceEth).toFixed(4));
      
      // Get chain ID
      const network = await provider.getNetwork();
      setChainId(Number(network.chainId));
      
      // Try to resolve ENS name
      try {
        const ens = await provider.lookupAddress(walletAddress);
        setEnsName(ens);
      } catch (e) {
        // ENS resolution failed, that's okay
        setEnsName(null);
      }
    } catch (error) {
      console.error('Error getting wallet info:', error);
    }
  };

  const disconnectWallet = () => {
    setAddress('');
    setBalance(null);
    setChainId(null);
    setEnsName(null);
    setWalletType('');
    onAddressSelect('');
  };

  const getChainName = (chainId) => {
    const chains = {
      1: 'Ethereum Mainnet',
      5: 'Goerli Testnet',
      11155111: 'Sepolia Testnet',
      137: 'Polygon',
      80001: 'Mumbai Testnet',
      56: 'BSC Mainnet',
      97: 'BSC Testnet'
    };
    return chains[chainId] || `Chain ID: ${chainId}`;
  };

  const addToWatchlist = () => {
    // This would integrate with the AI agent to add the wallet to monitoring
    onAddressSelect(address, { action: 'monitor' });
  };

  const copyAddress = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatAddress = (addr) => {
    return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
  };

  return (
    <div className="space-y-4">
      {!address ? (
        <div className="space-y-4">
          <button
            onClick={connectWallet}
            disabled={isConnecting}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            {isConnecting ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Link2 className="w-5 h-5" />
                Connect Wallet
              </>
            )}
          </button>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5" />
              <p className="text-xs text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Or try demo addresses:</p>
            <div className="space-y-1">
              <button
                onClick={() => onAddressSelect('0xDEMO0001')}
                className="w-full text-left px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-xs"
              >
                <code>0xDEMO0001</code>
                <span className="text-gray-500 ml-2">(Demo)</span>
              </button>
              <button
                onClick={() => onAddressSelect('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb4')}
                className="w-full text-left px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-xs"
              >
                <code>0x742d35...5f0bEb4</code>
                <span className="text-gray-500 ml-2">(Example)</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-300">{walletType}</p>
                  {chainId && (
                    <p className="text-xs text-green-600 dark:text-green-400">{getChainName(chainId)}</p>
                  )}
                </div>
              </div>
              <button
                onClick={disconnectWallet}
                className="px-2 py-1 text-xs bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              >
                Disconnect
              </button>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Address</p>
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-sm font-medium">{formatAddress(address)}</p>
                    {ensName && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{ensName}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={copyAddress}
                  className="p-1 hover:bg-white/50 dark:hover:bg-gray-700/50 rounded transition-colors"
                  title="Copy address"
                >
                  {copied ? (
                    <CheckCircle className="w-3 h-3 text-green-600" />
                  ) : (
                    <Copy className="w-3 h-3 text-gray-600" />
                  )}
                </button>
              </div>
              
              {balance !== null && (
                <div className="flex items-center justify-between pt-2 border-t border-green-200 dark:border-green-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Balance</p>
                  <p className="text-sm font-medium">{balance} ETH</p>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onAddressSelect(address)}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 px-3 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 flex items-center justify-center gap-2 text-sm"
            >
              <Shield className="w-4 h-4" />
              Analyze
            </button>
            <button
              onClick={addToWatchlist}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white py-2 px-3 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 flex items-center justify-center gap-2 text-sm"
            >
              <Activity className="w-4 h-4" />
              Monitor
            </button>
          </div>
          
          <div className="text-center">
            <a
              href={`https://etherscan.io/address/${address}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center justify-center gap-1"
            >
              View on Etherscan <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

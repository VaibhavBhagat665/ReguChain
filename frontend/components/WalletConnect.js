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

    // Check if MetaMask is installed
    if (typeof window.ethereum === 'undefined') {
      setError('Please install MetaMask, Coinbase Wallet, or another Web3 wallet');
      setIsConnecting(false);
      return;
    }

    try {
      // Create provider
      const provider = new ethers.BrowserProvider(window.ethereum);
      
      // Request account access
      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });
      
      if (accounts.length > 0) {
        const connectedAddress = accounts[0];
        setAddress(connectedAddress);
        
        // Get additional wallet info
        await getWalletInfo(provider, connectedAddress);
        
        // Detect wallet type
        if (window.ethereum.isMetaMask) {
          setWalletType('MetaMask');
        } else if (window.ethereum.isCoinbaseWallet) {
          setWalletType('Coinbase Wallet');
        } else {
          setWalletType('Web3 Wallet');
        }
        
        onAddressSelect(connectedAddress);
      }
    } catch (err) {
      if (err.code === 4001) {
        setError('Connection rejected by user');
      } else if (err.code === -32002) {
        setError('Please open your wallet and accept the connection');
      } else {
        setError('Failed to connect wallet: ' + (err.message || 'Unknown error'));
      }
      console.error('Error connecting wallet:', err);
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Wallet className="w-5 h-5 text-primary-600" />
        Wallet Connection
      </h2>

      {!address ? (
        <div>
          <button
            onClick={connectWallet}
            disabled={isConnecting}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center gap-2"
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
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          <div className="mt-4 space-y-3">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p className="font-medium mb-2">Or check these test addresses:</p>
              <div className="space-y-2">
                <button
                  onClick={() => onAddressSelect('0xDEMO0001')}
                  className="w-full text-left px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                >
                  <code className="text-xs">0xDEMO0001</code>
                  <span className="text-xs text-gray-500 ml-2">(Test wallet)</span>
                </button>
                <button
                  onClick={() => onAddressSelect('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb4')}
                  className="w-full text-left px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                >
                  <code className="text-xs">0x742d35...5f0bEb4</code>
                  <span className="text-xs text-gray-500 ml-2">(Example)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-300">Connected via {walletType}</p>
                  {chainId && (
                    <p className="text-xs text-green-600 dark:text-green-400">{getChainName(chainId)}</p>
                  )}
                </div>
              </div>
              <button
                onClick={disconnectWallet}
                className="px-3 py-1 text-xs bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              >
                Disconnect
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Address</p>
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-sm font-medium">{formatAddress(address)}</p>
                    {ensName && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{ensName}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={copyAddress}
                  className="p-2 hover:bg-white/50 dark:hover:bg-gray-700/50 rounded-lg transition-colors"
                  title="Copy address"
                >
                  {copied ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-600" />
                  )}
                </button>
              </div>
              
              {balance !== null && (
                <div className="flex items-center justify-between py-2 border-t border-green-200 dark:border-green-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Balance</p>
                  <p className="text-sm font-medium">{balance} ETH</p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <button
              onClick={() => onAddressSelect(address)}
              className="bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 transition-colors duration-200 flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4" />
              Analyze Wallet
            </button>
            <button
              onClick={addToWatchlist}
              className="bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center gap-2"
            >
              <Activity className="w-4 h-4" />
              Monitor
            </button>
          </div>
          
          <div className="mt-3 flex justify-center">
            <a
              href={`https://etherscan.io/address/${address}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              View on Etherscan <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-xs text-blue-800 dark:text-blue-300">
              <strong>Privacy & Security:</strong> Your wallet is connected securely via Web3. 
              We only read public blockchain data - no private keys or transactions are accessed.
              All analysis uses publicly available regulatory databases.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount } from 'wagmi';
import { useEffect } from 'react';

export default function WalletConnect({ onAddressSelect }) {
  const { address, isConnected } = useAccount();

  // Notify parent when connection changes
  useEffect(() => {
    if (isConnected && address) {
      onAddressSelect(address);
    } else {
      onAddressSelect('');
    }
  }, [address, isConnected, onAddressSelect]);

  return (
    <div className="w-full">
      <ConnectButton.Custom>
        {({
          account,
          chain,
          openAccountModal,
          openChainModal,
          openConnectModal,
          mounted,
        }) => {
          const ready = mounted;
          const connected = ready && account && chain;

          return (
            <div
              {...(!ready && {
                'aria-hidden': true,
                style: {
                  opacity: 0,
                  pointerEvents: 'none',
                  userSelect: 'none',
                },
              })}
              className="w-full"
            >
              {(() => {
                if (!connected) {
                  return (
                    <button
                      onClick={openConnectModal}
                      className="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white py-4 px-6 rounded-xl hover:from-blue-700 hover:to-cyan-600 transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transform hover:scale-[1.02] font-semibold text-lg"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      Connect Wallet
                    </button>
                  );
                }

                if (chain.unsupported) {
                  return (
                    <button
                      onClick={openChainModal}
                      className="w-full bg-red-500 text-white py-3 px-4 rounded-xl hover:bg-red-600 transition-colors"
                    >
                      Wrong network - Click to switch
                    </button>
                  );
                }

                return (
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
                    <div className="flex items-center justify-between mb-3">
                      <button
                        onClick={openChainModal}
                        className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
                      >
                        {chain.hasIcon && (
                          <div className="w-5 h-5 rounded-full overflow-hidden">
                            {chain.iconUrl && (
                              <img
                                alt={chain.name ?? 'Chain icon'}
                                src={chain.iconUrl}
                                className="w-5 h-5"
                              />
                            )}
                          </div>
                        )}
                        <span className="text-sm font-medium">{chain.name}</span>
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    </div>

                    <button
                      onClick={openAccountModal}
                      className="w-full flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
                          {account.displayName.substring(0, 2)}
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-semibold text-slate-900 dark:text-white">
                            {account.displayName}
                          </p>
                          {account.displayBalance && (
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                              {account.displayBalance}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                        Manage
                      </span>
                    </button>
                  </div>
                );
              })()}
            </div>
          );
        }}
      </ConnectButton.Custom>
    </div>
  );
}

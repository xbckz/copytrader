export function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatPercentage(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export function formatAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function calculateGasFee(gasUsed: number, gasPrice: number): number {
  // gasPrice in gwei, returns fee in ETH
  return (gasUsed * gasPrice) / 1e9;
}

export function ethToEur(ethAmount: number, ethPriceUsd: number, eurUsdRate: number): number {
  const usdAmount = ethAmount * ethPriceUsd;
  return usdAmount / eurUsdRate;
}

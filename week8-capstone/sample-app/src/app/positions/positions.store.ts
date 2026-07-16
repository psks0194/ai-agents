import { computed } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';

export interface Position {
  id: number;
  symbol: string;
  qty: number;
  price: number;
}

const SEED: Position[] = [
  { id: 1, symbol: 'AAPL', qty: 120, price: 214.3 },
  { id: 2, symbol: 'MSFT', qty: 80, price: 431.2 },
  { id: 3, symbol: 'NVDA', qty: 40, price: 126.5 },
];

export const PositionsStore = signalStore(
  { providedIn: 'root' },
  withState<{ positions: Position[]; filter: string }>({ positions: SEED, filter: '' }),
  withComputed(({ positions, filter }) => ({
    visible: computed(() =>
      positions().filter((p) => p.symbol.toLowerCase().includes(filter().toLowerCase())),
    ),
    totalValue: computed(() => positions().reduce((sum, p) => sum + p.qty * p.price, 0)),
  })),
  withMethods((store) => ({
    setFilter(filter: string): void {
      patchState(store, { filter });
    },
    addLot(id: number, qty: number): void {
      patchState(store, {
        positions: store.positions().map((p) => (p.id === id ? { ...p, qty: p.qty + qty } : p)),
      });
    },
  })),
);

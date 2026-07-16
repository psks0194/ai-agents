import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AgGridAngular } from 'ag-grid-angular';
import {
  AllCommunityModule,
  ColDef,
  ModuleRegistry,
  ValueFormatterParams,
  ValueGetterParams,
} from 'ag-grid-community';
import { Position, PositionsStore } from './positions.store';

ModuleRegistry.registerModules([AllCommunityModule]);

const money = (p: ValueFormatterParams): string => `$${Number(p.value).toFixed(2)}`;

@Component({
  selector: 'app-positions',
  imports: [FormsModule, AgGridAngular],
  templateUrl: './positions.html',
})
export class Positions {
  protected readonly store = inject(PositionsStore);

  protected readonly columns: ColDef<Position>[] = [
    { field: 'symbol', headerName: 'Symbol', sortable: true },
    { field: 'qty', headerName: 'Qty' },
    { field: 'price', headerName: 'Price', valueFormatter: money },
    {
      headerName: 'Value',
      valueGetter: (p: ValueGetterParams<Position>) => (p.data ? p.data.qty * p.data.price : 0),
      valueFormatter: money,
    },
  ];
}

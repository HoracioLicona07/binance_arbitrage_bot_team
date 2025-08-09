# binance_arbitrage_bot/binance_api/order_executor.py

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from binance.exceptions import BinanceAPIException
from binance_api.client import client
from strategies.triangular import format_quantity
from core.utils import fee_of

@dataclass
class OrderResult:
    """Resultado de una orden ejecutada"""
    success: bool
    order_id: Optional[str]
    symbol: str
    side: str
    quantity: float
    price: float
    executed_qty: float
    status: str
    error_message: Optional[str]
    execution_time: float

@dataclass
class ArbitrageExecution:
    """Resultado completo de una ejecución de arbitraje"""
    success: bool
    route: List[str]
    initial_amount: float
    final_amount: float
    net_profit: float
    total_fees: float
    execution_time: float
    orders: List[OrderResult]
    error_message: Optional[str]

class OrderExecutor:
    def __init__(self):
        self.max_retry_attempts = 3
        self.retry_delay = 0.1  # 100ms entre reintentos
        self.order_timeout = 30  # 30 segundos timeout por orden
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_profit': 0.0,
            'avg_execution_time': 0.0
        }
        
    def execute_arbitrage_atomic(self, route: List[str], amount: float, 
                               max_slippage: float = 0.02) -> ArbitrageExecution:
        """
        Ejecuta arbitraje de forma atómica con rollback automático
        
        Args:
            route: Ruta de arbitraje ['USDT', 'BTC', 'ETH', 'USDT']
            amount: Cantidad inicial en USDT
            max_slippage: Slippage máximo permitido (2% por defecto)
            
        Returns:
            ArbitrageExecution: Resultado completo de la ejecución
        """
        execution_start = time.time()
        orders = []
        
        try:
            logging.info(f"🚀 Iniciando arbitraje atómico: {' → '.join(route)} | {amount:.2f} USDT")
            
            # 1. Validar ruta antes de ejecutar
            if not self._validate_route(route, amount):
                return ArbitrageExecution(
                    success=False,
                    route=route,
                    initial_amount=amount,
                    final_amount=0.0,
                    net_profit=0.0,
                    total_fees=0.0,
                    execution_time=time.time() - execution_start,
                    orders=orders,
                    error_message="Validación de ruta fallida"
                )
            
            # 2. Determinar estrategia de ejecución
            execution_strategy = self._determine_execution_strategy(route, amount)
            
            if execution_strategy == 'margin':
                return self._execute_margin_arbitrage(route, amount, max_slippage)
            else:
                return self._execute_spot_arbitrage(route, amount, max_slippage)
                
        except Exception as e:
            logging.error(f"❌ Error crítico en ejecución atómica: {e}")
            
            # Rollback automático (sin async)
            self._rollback_partial_execution(orders)
            
            return ArbitrageExecution(
                success=False,
                route=route,
                initial_amount=amount,
                final_amount=0.0,
                net_profit=0.0,
                total_fees=0.0,
                execution_time=time.time() - execution_start,
                orders=orders,
                error_message=str(e)
            )
        finally:
            # Actualizar estadísticas
            self.execution_stats['total_executions'] += 1
    
    def _execute_spot_arbitrage(self, route: List[str], amount: float, 
                              max_slippage: float) -> ArbitrageExecution:
        """Ejecuta arbitraje usando trading spot"""
        execution_start = time.time()
        orders = []
        current_amount = amount
        total_fees = 0.0
        
        try:
            # Verificar balance inicial
            if not self._check_sufficient_balance(route[0], amount):
                return ArbitrageExecution(
                    success=False,
                    route=route,
                    initial_amount=amount,
                    final_amount=0.0,
                    net_profit=0.0,
                    total_fees=0.0,
                    execution_time=time.time() - execution_start,
                    orders=orders,
                    error_message=f"Balance insuficiente de {route[0]}"
                )
            
            # Ejecutar cada paso de la ruta
            for i in range(len(route) - 1):
                asset_from, asset_to = route[i], route[i + 1]
                
                # Determinar símbolo y dirección
                symbol, side = self._get_trading_pair(asset_from, asset_to)
                if not symbol:
                    raise Exception(f"No se encontró par trading para {asset_from}->{asset_to}")
                
                # Calcular cantidad a tradear
                if side == 'BUY':
                    # Comprando asset_to con asset_from
                    quantity = current_amount  # Cantidad en asset_from (quote)
                else:
                    # Vendiendo asset_from por asset_to  
                    quantity = current_amount  # Cantidad en asset_from (base)
                
                # Formatear cantidad según filtros del símbolo
                formatted_qty = format_quantity(symbol, quantity)
                
                # Ejecutar orden
                order_result = self._execute_market_order(
                    symbol, side, formatted_qty, max_slippage
                )
                orders.append(order_result)
                
                if not order_result.success:
                    raise Exception(f"Orden fallida en paso {i+1}: {order_result.error_message}")
                
                # Actualizar cantidad para siguiente paso
                if side == 'BUY':
                    current_amount = order_result.executed_qty
                else:
                    current_amount = order_result.executed_qty * order_result.price
                
                # Acumular fees
                fee_amount = current_amount * fee_of(symbol)
                total_fees += fee_amount
                current_amount -= fee_amount
                
                logging.info(f"✅ Paso {i+1}: {asset_from} → {asset_to} | Cantidad: {current_amount:.6f}")
            
            # Calcular resultado final
            net_profit = current_amount - amount
            execution_time = time.time() - execution_start
            
            # Actualizar estadísticas
            self.execution_stats['successful_executions'] += 1
            self.execution_stats['total_profit'] += net_profit
            self._update_avg_execution_time(execution_time)
            
            logging.info(f"🎉 Arbitraje completado: +{net_profit:.4f} USDT en {execution_time:.2f}s")
            
            return ArbitrageExecution(
                success=True,
                route=route,
                initial_amount=amount,
                final_amount=current_amount,
                net_profit=net_profit,
                total_fees=total_fees,
                execution_time=execution_time,
                orders=orders,
                error_message=None
            )
            
        except Exception as e:
            self.execution_stats['failed_executions'] += 1
            logging.error(f"❌ Error en arbitraje spot: {e}")
            
            return ArbitrageExecution(
                success=False,
                route=route,
                initial_amount=amount,
                final_amount=current_amount,
                net_profit=current_amount - amount,
                total_fees=total_fees,
                execution_time=time.time() - execution_start,
                orders=orders,
                error_message=str(e)
            )
    
    def _execute_margin_arbitrage(self, route: List[str], amount: float, 
                                max_slippage: float) -> ArbitrageExecution:
        """Ejecuta arbitraje usando margin trading"""
        execution_start = time.time()
        orders = []
        borrowed_assets = {}
        total_fees = 0.0
        
        try:
            # Para arbitraje triangular con margin: USDT -> BTC -> ETH -> USDT
            if len(route) != 4 or route[0] != 'USDT' or route[-1] != 'USDT':
                raise Exception("Margin arbitrage solo soporta rutas triangulares que empiecen y terminen en USDT")
            
            asset1, asset2 = route[1], route[2]  # BTC, ETH
            
            # 1. Pedir prestado asset1 (BTC)
            borrow_amount = self._calculate_borrow_amount(asset1, amount)
            borrow_result = self._borrow_margin_asset(asset1, borrow_amount)
            if not borrow_result:
                raise Exception(f"Error pidiendo prestado {asset1}")
            
            borrowed_assets[asset1] = borrow_amount
            current_amount = borrow_amount
            
            # 2. Vender asset1 por asset2 (BTC -> ETH)
            symbol1 = f"{asset1}{asset2}"
            order1 = self._execute_margin_order(symbol1, 'SELL', current_amount, max_slippage)
            orders.append(order1)
            
            if not order1.success:
                raise Exception(f"Error en paso 1: {order1.error_message}")
            
            current_amount = order1.executed_qty
            
            # 3. Vender asset2 por USDT (ETH -> USDT)
            symbol2 = f"{asset2}USDT"
            order2 = self._execute_margin_order(symbol2, 'SELL', current_amount, max_slippage)
            orders.append(order2)
            
            if not order2.success:
                raise Exception(f"Error en paso 2: {order2.error_message}")
            
            final_usdt = order2.executed_qty * order2.price
            
            # 4. Repagar préstamo
            repay_result = self._repay_margin_asset(asset1, borrow_amount)
            if not repay_result:
                raise Exception(f"Error repagando {asset1}")
            
            borrowed_assets.pop(asset1, None)
            
            # Calcular resultado
            net_profit = final_usdt - amount
            execution_time = time.time() - execution_start
            
            # Actualizar estadísticas
            self.execution_stats['successful_executions'] += 1
            self.execution_stats['total_profit'] += net_profit
            self._update_avg_execution_time(execution_time)
            
            logging.info(f"🎉 Margin arbitraje completado: +{net_profit:.4f} USDT en {execution_time:.2f}s")
            
            return ArbitrageExecution(
                success=True,
                route=route,
                initial_amount=amount,
                final_amount=final_usdt,
                net_profit=net_profit,
                total_fees=total_fees,
                execution_time=execution_time,
                orders=orders,
                error_message=None
            )
            
        except Exception as e:
            self.execution_stats['failed_executions'] += 1
            logging.error(f"❌ Error en margin arbitraje: {e}")
            
            # Rollback: repagar cualquier préstamo pendiente
            for asset, amount_borrowed in borrowed_assets.items():
                try:
                    self._repay_margin_asset(asset, amount_borrowed)
                    logging.info(f"🔄 Rollback: {asset} repagado")
                except Exception as rollback_error:
                    logging.error(f"❌ Error en rollback {asset}: {rollback_error}")
            
            return ArbitrageExecution(
                success=False,
                route=route,
                initial_amount=amount,
                final_amount=0.0,
                net_profit=-amount,  # Pérdida conservadora
                total_fees=total_fees,
                execution_time=time.time() - execution_start,
                orders=orders,
                error_message=str(e)
            )
    
    def _execute_market_order(self, symbol: str, side: str, quantity: float, 
                            max_slippage: float) -> OrderResult:
        """Ejecuta una orden de mercado con validación de slippage"""
        order_start = time.time()
        
        try:
            # Obtener precio actual para validar slippage
            ticker = client.get_symbol_ticker(symbol=symbol)
            expected_price = float(ticker['price'])
            
            # Ejecutar orden
            for attempt in range(self.max_retry_attempts):
                try:
                    if side == 'BUY':
                        order = client.order_market_buy(
                            symbol=symbol,
                            quoteOrderQty=quantity
                        )
                    else:
                        order = client.order_market_sell(
                            symbol=symbol,
                            quantity=quantity
                        )
                    
                    # Validar ejecución
                    executed_qty = float(order['executedQty'])
                    if executed_qty == 0:
                        raise Exception("Orden ejecutada con cantidad 0")
                    
                    # Calcular precio promedio ejecutado
                    fills = order.get('fills', [])
                    if fills:
                        total_qty = sum(float(fill['qty']) for fill in fills)
                        total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in fills)
                        avg_price = total_cost / total_qty if total_qty > 0 else expected_price
                    else:
                        avg_price = expected_price
                    
                    # Validar slippage
                    slippage = abs(avg_price - expected_price) / expected_price
                    if slippage > max_slippage:
                        logging.warning(f"⚠️ Alto slippage en {symbol}: {slippage:.4f} > {max_slippage:.4f}")
                    
                    execution_time = time.time() - order_start
                    
                    return OrderResult(
                        success=True,
                        order_id=str(order['orderId']),
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=avg_price,
                        executed_qty=executed_qty,
                        status=order['status'],
                        error_message=None,
                        execution_time=execution_time
                    )
                    
                except BinanceAPIException as e:
                    if attempt < self.max_retry_attempts - 1:
                        logging.warning(f"⚠️ Reintentando orden {symbol} (intento {attempt + 1}): {e}")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise e
            
        except Exception as e:
            execution_time = time.time() - order_start
            logging.error(f"❌ Error ejecutando orden {symbol} {side}: {e}")
            
            return OrderResult(
                success=False,
                order_id=None,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=0.0,
                executed_qty=0.0,
                status='FAILED',
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _execute_margin_order(self, symbol: str, side: str, quantity: float, 
                            max_slippage: float) -> OrderResult:
        """Ejecuta una orden de margin con validación"""
        order_start = time.time()
        
        try:
            # Formatear cantidad
            formatted_qty = format_quantity(symbol, quantity)
            
            for attempt in range(self.max_retry_attempts):
                try:
                    order = client.create_margin_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=formatted_qty
                    )
                    
                    executed_qty = float(order['executedQty'])
                    avg_price = float(order['price']) if 'price' in order else 0.0
                    
                    # Si no hay precio en la respuesta, calcularlo de los fills
                    if avg_price == 0.0 and 'fills' in order:
                        fills = order['fills']
                        if fills:
                            total_qty = sum(float(fill['qty']) for fill in fills)
                            total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in fills)
                            avg_price = total_cost / total_qty if total_qty > 0 else 0.0
                    
                    execution_time = time.time() - order_start
                    
                    return OrderResult(
                        success=True,
                        order_id=str(order['orderId']),
                        symbol=symbol,
                        side=side,
                        quantity=formatted_qty,
                        price=avg_price,
                        executed_qty=executed_qty,
                        status=order['status'],
                        error_message=None,
                        execution_time=execution_time
                    )
                    
                except BinanceAPIException as e:
                    if attempt < self.max_retry_attempts - 1:
                        logging.warning(f"⚠️ Reintentando margin orden (intento {attempt + 1}): {e}")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            execution_time = time.time() - order_start
            logging.error(f"❌ Error ejecutando margin orden {symbol}: {e}")
            
            return OrderResult(
                success=False,
                order_id=None,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=0.0,
                executed_qty=0.0,
                status='FAILED',
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _validate_route(self, route: List[str], amount: float) -> bool:
        """Valida que la ruta sea ejecutable"""
        try:
            # Verificar longitud mínima
            if len(route) < 3:
                logging.error("❌ Ruta muy corta")
                return False
            
            # Verificar que empiece y termine con el mismo asset
            if route[0] != route[-1]:
                logging.error("❌ Ruta debe empezar y terminar con el mismo asset")
                return False
            
            # Verificar que todos los pares existan
            for i in range(len(route) - 1):
                asset_from, asset_to = route[i], route[i + 1]
                symbol, _ = self._get_trading_pair(asset_from, asset_to)
                if not symbol:
                    logging.error(f"❌ Par {asset_from}-{asset_to} no existe")
                    return False
            
            # Verificar cantidad mínima
            if amount < 10:  # Mínimo 10 USDT
                logging.error("❌ Cantidad muy pequeña")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error validando ruta: {e}")
            return False
    
    def _determine_execution_strategy(self, route: List[str], amount: float) -> str:
        """Determina si usar spot o margin trading"""
        # Usar margin solo para rutas triangulares específicas
        if (len(route) == 4 and 
            route[0] == 'USDT' and 
            route[-1] == 'USDT' and
            amount >= 50):  # Mínimo para margin
            return 'margin'
        else:
            return 'spot'
    
    def _get_trading_pair(self, asset_from: str, asset_to: str) -> Tuple[Optional[str], Optional[str]]:
        """Encuentra el par de trading y la dirección"""
        # Intentar ambas combinaciones
        fwd_symbol = asset_from + asset_to
        rev_symbol = asset_to + asset_from
        
        try:
            if client.get_symbol_info(fwd_symbol):
                return fwd_symbol, 'SELL'  # Vendemos asset_from
        except:
            pass
        
        try:
            if client.get_symbol_info(rev_symbol):
                return rev_symbol, 'BUY'   # Compramos asset_to
        except:
            pass
        
        return None, None
    
    def _check_sufficient_balance(self, asset: str, required_amount: float) -> bool:
        """Verifica si hay balance suficiente"""
        try:
            account = client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    free_balance = float(balance['free'])
                    return free_balance >= required_amount
            return False
        except Exception as e:
            logging.error(f"❌ Error verificando balance: {e}")
            return False
    
    def _calculate_borrow_amount(self, asset: str, usdt_amount: float) -> float:
        """Calcula cantidad a pedir prestado"""
        try:
            ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
            price = float(ticker['price'])
            borrow_amount = usdt_amount / price
            return format_quantity(f"{asset}USDT", borrow_amount)
        except Exception as e:
            logging.error(f"❌ Error calculando cantidad a pedir prestado: {e}")
            return 0.0
    
    def _borrow_margin_asset(self, asset: str, amount: float) -> bool:
        """Pide prestado un asset en margin"""
        try:
            formatted_amount = format_quantity(f"{asset}USDT", amount)
            result = client.create_margin_loan(asset=asset, amount=formatted_amount)
            logging.info(f"💰 Prestado: {formatted_amount} {asset}")
            return True
        except Exception as e:
            logging.error(f"❌ Error pidiendo prestado {asset}: {e}")
            return False
    
    def _repay_margin_asset(self, asset: str, amount: float) -> bool:
        """Repaga un préstamo margin"""
        try:
            formatted_amount = format_quantity(f"{asset}USDT", amount)
            result = client.repay_margin_loan(asset=asset, amount=formatted_amount)
            logging.info(f"✅ Repagado: {formatted_amount} {asset}")
            return True
        except Exception as e:
            logging.error(f"❌ Error repagando {asset}: {e}")
            return False
    
    def _rollback_partial_execution(self, orders: List[OrderResult]):
        """Rollback de una ejecución parcial (versión sincrónica)"""
        logging.warning("🔄 Iniciando rollback de ejecución parcial...")
        
        # TODO: Implementar reversión de órdenes si es necesario
        # Por ahora solo loggear
        for order in orders:
            if order.success:
                logging.info(f"🔄 Orden a revertir: {order.symbol} {order.side} {order.executed_qty}")
        
        logging.info("🔄 Rollback completado")
    
    def _update_avg_execution_time(self, execution_time: float):
        """Actualiza tiempo promedio de ejecución"""
        total_execs = self.execution_stats['total_executions']
        current_avg = self.execution_stats['avg_execution_time']
        
        # Promedio ponderado
        if total_execs > 0:
            new_avg = ((current_avg * (total_execs - 1)) + execution_time) / total_execs
            self.execution_stats['avg_execution_time'] = new_avg
        else:
            self.execution_stats['avg_execution_time'] = execution_time
    
    def get_execution_stats(self) -> Dict:
        """Obtiene estadísticas de ejecución"""
        total_execs = self.execution_stats['total_executions']
        successful_execs = self.execution_stats['successful_executions']
        
        success_rate = (successful_execs / total_execs * 100) if total_execs > 0 else 0.0
        
        return {
            'total_executions': total_execs,
            'successful_executions': successful_execs,
            'failed_executions': self.execution_stats['failed_executions'],
            'success_rate_pct': success_rate,
            'total_profit_usdt': self.execution_stats['total_profit'],
            'avg_execution_time_sec': self.execution_stats['avg_execution_time'],
            'avg_profit_per_trade': (
                self.execution_stats['total_profit'] / successful_execs 
                if successful_execs > 0 else 0.0
            )
        }
    
    def reset_stats(self):
        """Resetea estadísticas de ejecución"""
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_profit': 0.0,
            'avg_execution_time': 0.0
        }
        logging.info("📊 Estadísticas de ejecución reseteadas")

# Instancia global del ejecutor
order_executor = OrderExecutor()
# binance_arbitrage_bot/binance_api/fee_manager.py

import logging
import time
from typing import Dict, Optional
from binance_api.client import client

class FeeManager:
    def __init__(self):
        self.fee_cache = {}
        self.cache_duration = 3600  # 1 hora
        self.last_cache_update = 0
        self.user_fee_tier = None
        self.bnb_discount = False
        self.default_fees = {
            'maker': 0.001,  # 0.1%
            'taker': 0.001   # 0.1%
        }
        self.vip_fee_schedule = {
            0: {'maker': 0.001, 'taker': 0.001},   # Regular
            1: {'maker': 0.0009, 'taker': 0.001},  # VIP 1
            2: {'maker': 0.0008, 'taker': 0.001},  # VIP 2
            3: {'maker': 0.0007, 'taker': 0.001},  # VIP 3
            4: {'maker': 0.0007, 'taker': 0.0009}, # VIP 4
            5: {'maker': 0.0006, 'taker': 0.0008}, # VIP 5
            6: {'maker': 0.0005, 'taker': 0.0007}, # VIP 6
            7: {'maker': 0.0004, 'taker': 0.0006}, # VIP 7
            8: {'maker': 0.0003, 'taker': 0.0005}, # VIP 8
            9: {'maker': 0.0002, 'taker': 0.0004}  # VIP 9
        }
        self._initialize_user_fees()
    
    def _initialize_user_fees(self):
        """Inicializa las comisiones del usuario actual"""
        try:
            # Obtener información de la cuenta
            account_info = client.get_account()
            
            # Obtener tier de comisiones
            self.user_fee_tier = self._determine_fee_tier(account_info)
            
            # Verificar si tiene descuento BNB
            self.bnb_discount = self._check_bnb_discount(account_info)
            
            # Obtener comisiones específicas por símbolo
            self._update_trading_fees()
            
            logging.info(f"📊 Usuario VIP nivel: {self.user_fee_tier}")
            logging.info(f"💰 Descuento BNB activo: {self.bnb_discount}")
            
        except Exception as e:
            logging.warning(f"⚠️ No se pudieron obtener comisiones del usuario: {e}")
            logging.info("📊 Usando comisiones por defecto")
    
    def _determine_fee_tier(self, account_info: Dict) -> int:
        """Determina el tier VIP basado en el volumen de trading"""
        try:
            # Intentar obtener el tier directamente (si está disponible)
            if 'vipLevel' in account_info:
                return account_info['vipLevel']
            
            # Calcular basado en volumen (aproximación)
            # Nota: Binance no siempre provee esta info directamente
            # Se puede implementar lógica adicional aquí
            return 0  # Tier regular por defecto
            
        except Exception as e:
            logging.warning(f"⚠️ Error determinando tier VIP: {e}")
            return 0
    
    def _check_bnb_discount(self, account_info: Dict) -> bool:
        """Verifica si el descuento BNB está activo"""
        try:
            # Verificar si el usuario tiene BNB y descuento activo
            bnb_balance = 0
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'BNB':
                    bnb_balance = float(balance['free'])
                    break
            
            # Necesita al menos algo de BNB para descuento
            return bnb_balance > 0.1
            
        except Exception as e:
            logging.warning(f"⚠️ Error verificando descuento BNB: {e}")
            return False
    
    def _update_trading_fees(self):
        """Actualiza las comisiones específicas por símbolo"""
        try:
            # Intentar obtener comisiones específicas
            trade_fee = client.get_trade_fee()
            
            current_time = time.time()
            for fee_info in trade_fee:
                symbol = fee_info['symbol']
                self.fee_cache[symbol] = {
                    'maker': float(fee_info['makerCommission']),
                    'taker': float(fee_info['takerCommission']),
                    'timestamp': current_time
                }
            
            self.last_cache_update = current_time
            logging.info(f"📊 Comisiones actualizadas para {len(self.fee_cache)} símbolos")
            
        except Exception as e:
            logging.warning(f"⚠️ Error obteniendo comisiones específicas: {e}")
            # Usar comisiones por tier VIP como fallback
            self._use_vip_fees()
    
    def _use_vip_fees(self):
        """Usa las comisiones basadas en tier VIP como fallback"""
        if self.user_fee_tier in self.vip_fee_schedule:
            base_fees = self.vip_fee_schedule[self.user_fee_tier]
            
            # Aplicar descuento BNB si está activo (25% de descuento)
            if self.bnb_discount:
                self.default_fees = {
                    'maker': base_fees['maker'] * 0.75,
                    'taker': base_fees['taker'] * 0.75
                }
            else:
                self.default_fees = base_fees.copy()
    
    def get_trading_fee(self, symbol: str, is_maker: bool = False) -> float:
        """
        Obtiene la comisión de trading para un símbolo específico
        
        Args:
            symbol: Símbolo del par de trading
            is_maker: True si es orden maker, False si es taker
            
        Returns:
            Comisión como decimal (ej: 0.001 = 0.1%)
        """
        try:
            # Verificar cache
            current_time = time.time()
            
            if symbol in self.fee_cache:
                fee_data = self.fee_cache[symbol]
                if current_time - fee_data['timestamp'] < self.cache_duration:
                    return fee_data['maker'] if is_maker else fee_data['taker']
            
            # Si no está en cache o está obsoleto, usar fees por defecto
            fee_type = 'maker' if is_maker else 'taker'
            return self.default_fees[fee_type]
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo comisión para {symbol}: {e}")
            return 0.001  # Fallback conservador
    
    def get_arbitrage_total_fee(self, route: list, amount: float) -> float:
        """
        Calcula la comisión total para una ruta de arbitraje completa
        
        Args:
            route: Lista de assets en la ruta (ej: ['USDT', 'BTC', 'ETH', 'USDT'])
            amount: Cantidad inicial en USDT
            
        Returns:
            Comisión total como decimal
        """
        total_fee_cost = 0.0
        current_amount = amount
        
        try:
            for i in range(len(route) - 1):
                asset_from, asset_to = route[i], route[i + 1]
                
                # Determinar símbolo
                symbol = self._get_symbol_for_pair(asset_from, asset_to)
                if not symbol:
                    continue
                
                # Para arbitraje usamos órdenes market (taker)
                fee_rate = self.get_trading_fee(symbol, is_maker=False)
                
                # Calcular costo de comisión para este paso
                fee_cost = current_amount * fee_rate
                total_fee_cost += fee_cost
                
                # Actualizar cantidad para siguiente paso (estimación)
                current_amount -= fee_cost
            
            return total_fee_cost / amount  # Retornar como porcentaje del monto inicial
            
        except Exception as e:
            logging.error(f"❌ Error calculando comisiones de arbitraje: {e}")
            return 0.003  # Estimación conservadora (0.3% total)
    
    def _get_symbol_for_pair(self, asset_from: str, asset_to: str) -> str:
        """Determina el símbolo correcto para un par de assets"""
        # Intentar ambas combinaciones
        fwd_symbol = asset_from + asset_to
        rev_symbol = asset_to + asset_from
        
        try:
            if client.get_symbol_info(fwd_symbol):
                return fwd_symbol
        except:
            pass
        
        try:
            if client.get_symbol_info(rev_symbol):
                return rev_symbol
        except:
            pass
        
        return None
    
    def estimate_fee_savings_with_bnb(self, monthly_volume_usdt: float) -> Dict:
        """
        Estima el ahorro en comisiones usando BNB
        
        Args:
            monthly_volume_usdt: Volumen mensual estimado en USDT
            
        Returns:
            Diccionario con análisis de ahorro
        """
        try:
            # Comisiones sin BNB
            base_fee_rate = self.default_fees['taker'] / 0.75 if self.bnb_discount else self.default_fees['taker']
            fees_without_bnb = monthly_volume_usdt * base_fee_rate
            
            # Comisiones con BNB (25% descuento)
            fees_with_bnb = monthly_volume_usdt * base_fee_rate * 0.75
            
            # Ahorro mensual
            monthly_savings = fees_without_bnb - fees_with_bnb
            annual_savings = monthly_savings * 12
            
            return {
                'monthly_volume_usdt': monthly_volume_usdt,
                'fees_without_bnb': fees_without_bnb,
                'fees_with_bnb': fees_with_bnb,
                'monthly_savings': monthly_savings,
                'annual_savings': annual_savings,
                'savings_percentage': 25.0,
                'recommendation': 'Usar BNB' if monthly_savings > 10 else 'No necesario'
            }
            
        except Exception as e:
            logging.error(f"❌ Error calculando ahorro BNB: {e}")
            return {}
    
    def get_fee_analysis(self) -> Dict:
        """Obtiene análisis completo de comisiones del usuario"""
        return {
            'user_vip_tier': self.user_fee_tier,
            'bnb_discount_active': self.bnb_discount,
            'current_maker_fee': self.default_fees['maker'],
            'current_taker_fee': self.default_fees['taker'],
            'cached_symbols': len(self.fee_cache),
            'cache_age_minutes': (time.time() - self.last_cache_update) / 60,
            'next_vip_tier_requirements': self._get_next_tier_requirements(),
            'optimization_tips': self._get_optimization_tips()
        }
    
    def _get_next_tier_requirements(self) -> Dict:
        """Obtiene los requisitos para el siguiente tier VIP"""
        if self.user_fee_tier >= 9:
            return {'message': 'Ya está en el tier máximo'}
        
        # Volúmenes aproximados para cada tier (en BTC)
        tier_requirements = {
            1: {'btc_volume': 100, 'bnb_balance': 50},
            2: {'btc_volume': 500, 'bnb_balance': 200},
            3: {'btc_volume': 1000, 'bnb_balance': 500},
            4: {'btc_volume': 2000, 'bnb_balance': 1000},
            5: {'btc_volume': 5000, 'bnb_balance': 2000},
            6: {'btc_volume': 10000, 'bnb_balance': 3500},
            7: {'btc_volume': 20000, 'bnb_balance': 6000},
            8: {'btc_volume': 40000, 'bnb_balance': 9000},
            9: {'btc_volume': 80000, 'bnb_balance': 11000}
        }
        
        next_tier = self.user_fee_tier + 1
        return tier_requirements.get(next_tier, {})
    
    def _get_optimization_tips(self) -> list:
        """Obtiene consejos para optimizar comisiones"""
        tips = []
        
        if not self.bnb_discount:
            tips.append("💡 Activar descuento BNB para 25% menos comisiones")
        
        if self.user_fee_tier == 0:
            tips.append("📈 Aumentar volumen de trading para acceder a tier VIP")
        
        if len(self.fee_cache) < 50:
            tips.append("🔄 Actualizar cache de comisiones para mayor precisión")
        
        # Verificar si hay comisiones altas en símbolos frecuentes
        high_fee_symbols = [
            symbol for symbol, data in self.fee_cache.items()
            if data.get('taker', 0) > 0.0015  # Mayor a 0.15%
        ]
        
        if high_fee_symbols:
            tips.append(f"⚠️ Evitar símbolos con comisiones altas: {', '.join(high_fee_symbols[:3])}")
        
        return tips
    
    def refresh_fees(self):
        """Actualiza manualmente todas las comisiones"""
        try:
            self._initialize_user_fees()
            logging.info("✅ Comisiones actualizadas manualmente")
        except Exception as e:
            logging.error(f"❌ Error actualizando comisiones: {e}")
    
    def get_symbol_fee_breakdown(self, symbol: str) -> Dict:
        """Obtiene desglose detallado de comisiones para un símbolo"""
        try:
            maker_fee = self.get_trading_fee(symbol, is_maker=True)
            taker_fee = self.get_trading_fee(symbol, is_maker=False)
            
            # Calcular ahorro potencial con órdenes maker
            maker_savings_pct = ((taker_fee - maker_fee) / taker_fee) * 100 if taker_fee > 0 else 0
            
            return {
                'symbol': symbol,
                'maker_fee': maker_fee,
                'taker_fee': taker_fee,
                'maker_fee_pct': maker_fee * 100,
                'taker_fee_pct': taker_fee * 100,
                'maker_savings_pct': maker_savings_pct,
                'is_cached': symbol in self.fee_cache,
                'bnb_discount_applied': self.bnb_discount
            }
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo desglose de {symbol}: {e}")
            return {}

# Instancia global del fee manager
fee_manager = FeeManager()

def get_trading_fee(symbol: str, is_maker: bool = False) -> float:
    """Función helper para obtener comisión de trading"""
    return fee_manager.get_trading_fee(symbol, is_maker)

def get_arbitrage_total_fee(route: list, amount: float) -> float:
    """Función helper para obtener comisión total de arbitraje"""
    return fee_manager.get_arbitrage_total_fee(route, amount)
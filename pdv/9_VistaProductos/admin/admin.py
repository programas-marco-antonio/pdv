from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.lang import Builder

from sqlqueries import QueriesSQLite

Builder.load_file('admin/admin.kv')

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    touch_deselect_last = BooleanProperty(True) 

class SelectableProductoLabel(RecycleDataViewBehavior, BoxLayout):
	index = None
	selected = BooleanProperty(False)
	selectable = BooleanProperty(True)

	def refresh_view_attrs(self, rv, index, data):
		self.index = index
		self.ids['_hashtag'].text = str(1+index)
		self.ids['_codigo'].text = data['codigo']
		self.ids['_articulo'].text = data['nombre'].capitalize()
		self.ids['_cantidad'].text = str(data['cantidad'])
		self.ids['_precio'].text = str("{:.2f}".format(data['precio']))
		return super(SelectableProductoLabel, self).refresh_view_attrs(
            rv, index, data)

	def on_touch_down(self, touch):
		if super(SelectableProductoLabel, self).on_touch_down(touch):
			return True
		if self.collide_point(*touch.pos) and self.selectable:
			return self.parent.select_with_touch(self.index, touch)

	def apply_selection(self, rv, index, is_selected):
		self.selected = is_selected
		if is_selected:
			rv.data[index]['seleccionado']=True
		else:
			rv.data[index]['seleccionado']=False

class SelectableUsuarioLabel(RecycleDataViewBehavior, BoxLayout):
	index = None
	selected = BooleanProperty(False)
	selectable = BooleanProperty(True)

	def refresh_view_attrs(self, rv, index, data):
		self.index = index
		self.ids['_hashtag'].text = str(1+index)
		self.ids['_nombre'].text = data['nombre'].title()
		self.ids['_username'].text = data['username']
		self.ids['_tipo'].text = str(data['tipo'])
		return super(SelectableUsuarioLabel, self).refresh_view_attrs(
            rv, index, data)

	def on_touch_down(self, touch):
		if super(SelectableUsuarioLabel, self).on_touch_down(touch):
			return True
		if self.collide_point(*touch.pos) and self.selectable:
			return self.parent.select_with_touch(self.index, touch)

	def apply_selection(self, rv, index, is_selected):
		self.selected = is_selected
		if is_selected:
			rv.data[index]['seleccionado']=True
		else:
			rv.data[index]['seleccionado']=False

class AdminRV(RecycleView):
    def __init__(self, **kwargs):
        super(AdminRV, self).__init__(**kwargs)
        self.data=[]

    def agregar_datos(self,datos):
        for dato in datos:
            dato['seleccionado']=False
            self.data.append(dato)
        self.refresh_from_data()

    def dato_seleccionado(self):
        indice=-1
        for i in range(len(self.data)):
            if self.data[i]['seleccionado']:
                indice=i
                break
        return indice

class ProductoPopup(Popup):
	def __init__(self, agregar_callback, **kwargs):
		super(ProductoPopup, self).__init__(**kwargs)
		self.agregar_callback=agregar_callback

	def abrir(self, agregar, producto=None):
		if agregar:
			self.ids.producto_info_1.text='Agregar producto nuevo'
			self.ids.producto_codigo.disabled=False
		else:
			self.ids.producto_info_1.text='Modificar producto'
			self.ids.producto_codigo.text=producto['codigo']
			self.ids.producto_codigo.disabled=True
			self.ids.producto_nombre.text=producto['nombre']
			self.ids.producto_cantidad.text=str(producto['cantidad'])
			self.ids.producto_precio.text=str(producto['precio'])
		self.open()

	def verificar(self, producto_codigo, producto_nombre, producto_cantidad, producto_precio):
		alert1='Falta: '
		alert2=''
		validado={}
		if not producto_codigo:
			alert1+='Codigo. '
			validado['codigo']=False
		else:
			try:
				numeric=int(producto_codigo)
				validado['codigo']=producto_codigo
			except:
				alert2+='Código no válido. '
				validado['codigo']=False

		if not producto_nombre:
			alert1+='Nombre. '
			validado['nombre']=False
		else:
			validado['nombre']=producto_nombre.lower()

		if not producto_precio:
			alert1+='Precio. '
			validado['precio']=False
		else:
			try:
				numeric=float(producto_precio)
				validado['precio']=producto_precio
			except:
				alert2+='Precio no válido. '
				validado['precio']=False
			
		if not producto_cantidad:
			alert1+='Cantidad. '
			validado['cantidad']=False
		else:
			try:
				numeric=int(producto_cantidad)
				validado['cantidad']=producto_cantidad
			except:
				alert2+='Cantidad no válida. '
				validado['cantidad']=False

		valores=list(validado.values())

		if False in valores:
			self.ids.no_valid_notif.text=alert1+alert2
		else:
			self.ids.no_valid_notif.text='Validado'
			validado['cantidad']=int(validado['cantidad'])
			validado['precio']=float(validado['precio'])
			self.agregar_callback(True, validado)
			self.dismiss()


class VistaProductos(Screen):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		Clock.schedule_once(self.cargar_productos, 1)

	def cargar_productos(self, *args):
		_productos=[]
		connection=QueriesSQLite.create_connection("pdvDB.sqlite")
		inventario_sql=QueriesSQLite.execute_read_query(connection, "SELECT * from productos")
		for producto in inventario_sql:
			_productos.append({'codigo': producto[0], 'nombre': producto[1], 'precio': producto[2], 'cantidad': producto[3]})
		self.ids.rv_productos.agregar_datos(_productos)

	def agregar_producto(self, agregar=False, validado=None):
		if agregar:
			producto_tuple=tuple(validado.values())
			connection=QueriesSQLite.create_connection("pdvDB.sqlite")
			crear_producto="""
			INSERT INTO
				productos (codigo, nombre, precio, cantidad)
			VALUES
				(?, ?, ?, ?);
			"""
			QueriesSQLite.execute_query(connection, crear_producto, producto_tuple)
			self.ids.rv_productos.data.append(validado)
			self.ids.rv_productos.refresh_from_data()
		else:
			popup=ProductoPopup(self.agregar_producto)
			popup.abrir(True)


	def modificar_producto(self, modificar=False, validado=None):
		indice=self.ids.rv_productos.dato_seleccionado()
		if modificar:
			producto_tuple=(validado['nombre'], validado['precio'], validado['cantidad'], validado['codigo'])
			connection=QueriesSQLite.create_connection("pdvDB.sqlite")
			actualizar="""
			UPDATE
				productos
			SET
				nombre=?, precio=?, cantidad=?
			WHERE
				codigo=?
			"""
			QueriesSQLite.execute_query(connection, actualizar, producto_tuple)
			self.ids.rv_productos.data[indice]['nombre']=validado['nombre']
			self.ids.rv_productos.data[indice]['cantidad']=validado['cantidad']
			self.ids.rv_productos.data[indice]['precio']=validado['precio']
			self.ids.rv_productos.refresh_from_data()
		else:
			if indice>=0:
				producto=self.ids.rv_productos.data[indice]
				popup=ProductoPopup(self.modificar_producto)
				popup.abrir(False, producto)


	def eliminar_producto(self):
		indice=self.ids.rv_productos.dato_seleccionado()
		if indice>=0:
			producto_tuple=(self.ids.rv_productos.data[indice]['codigo'],)
			connection=QueriesSQLite.create_connection("pdvDB.sqlite")
			borrar= """DELETE from productos WHERE codigo =? """
			QueriesSQLite.execute_query(connection, borrar, producto_tuple)
			self.ids.rv_productos.data.pop(indice)
			self.ids.rv_productos.refresh_from_data()




class VistaUsuarios(Screen):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		Clock.schedule_once(self.cargar_usuarios, 1)

	def cargar_usuarios(self, *args):
		_usuarios=[]
		connection=QueriesSQLite.create_connection("pdvDB.sqlite")
		usuarios_sql=QueriesSQLite.execute_read_query(connection, "SELECT * from usuarios")
		for usuario in usuarios_sql:
			_usuarios.append({'nombre': usuario[1], 'username': usuario[0], 'password': usuario[2], 'tipo': usuario[3]})
		self.ids.rv_usuarios.agregar_datos(_usuarios)

	def agregar_usuario(self):
		print("agregar usuario")

	def modificar_usuario(self):
		print("modificar usuario")
		

	def eliminar_usuario(self):
		print("elimnar usuario")



class AdminWindow(BoxLayout):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.vista_actual='Productos'
		self.vista_manager=self.ids.vista_manager
		
		
	def cambiar_vista(self):
		if self.vista_actual=='Productos':
			self.vista_actual='Usuarios'
		else:
			self.vista_actual='Productos'
		self.vista_manager.current=self.vista_actual

	def signout(self):
		self.parent.parent.current='scrn_signin'

	def venta(self):
		self.parent.parent.current='scrn_ventas'


class AdminApp(App):
	def build(self):
		return AdminWindow()

if __name__=="__main__":
    AdminApp().run() 

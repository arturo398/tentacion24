//Carrito de venta
let carrito = [];

//Tarjetas de productos
const tarjetas = document.querySelectorAll(".producto-card");

//Contenedores
const carritoDiv = document.getElementById("carrito");
const totalDiv = document.getElementById("total");
const mensajeDiv = document.getElementById("mensaje-pos");
const botonFinalizar = document.getElementById("btn-finalizar");
console.log("Botón encontrado:", botonFinalizar);

// Elementos de búsqueda y categorías
const searchInput = document.getElementById("pos-search");
const clienteNombreInput = document.getElementById("cliente-nombre");
const categoriaBotones = document.querySelectorAll(".btn-categoria");
const productoCols = document.querySelectorAll(".producto-col");

let categoriaSeleccionada = "todos";
let textoBusqueda = "";

function filtrarProductos() {
    productoCols.forEach(col => {
        const cat = col.dataset.categoria;
        const nombre = col.dataset.nombre;
        
        const cumpleCategoria = (categoriaSeleccionada === "todos" || cat === categoriaSeleccionada.toLowerCase());
        const cumpleBusqueda = nombre.includes(textoBusqueda.toLowerCase());
        
        if (cumpleCategoria && cumpleBusqueda) {
            col.style.display = "block";
        } else {
            col.style.display = "none";
        }
    });
}

if (searchInput) {
    searchInput.addEventListener("input", (e) => {
        textoBusqueda = e.target.value;
        filtrarProductos();
    });
}

categoriaBotones.forEach(boton => {
    boton.addEventListener("click", () => {
        categoriaBotones.forEach(b => {
            b.classList.remove("btn-dark");
            b.classList.add("btn-outline-dark");
        });
        boton.classList.remove("btn-outline-dark");
        boton.classList.add("btn-dark");
        
        categoriaSeleccionada = boton.dataset.categoria;
        filtrarProductos();
    });
});

//Eventos de las tarjetas
tarjetas.forEach((tarjeta) => {
    tarjeta.addEventListener("click", () => {
        agregarProducto(
            tarjeta.dataset.id,
            tarjeta.dataset.nombre,
            parseFloat(tarjeta.dataset.precio),
            parseInt(tarjeta.dataset.stock)
        );
    });
});

function agregarProducto(id, nombre, precio, stock) {
    const existente = carrito.find(
        producto => producto.id == id
    );

    const cantidadActual = existente ? existente.cantidad : 0;

    if(cantidadActual >= stock){
        alert("No hay suficiente stock disponible.");
        return;
    }

    // Aplicar animación a la tarjeta del producto
    const tarjeta = document.querySelector(`.producto-card[data-id="${id}"]`);
    if (tarjeta) {
        tarjeta.classList.add("pulse-animation");
        setTimeout(() => {
            tarjeta.classList.remove("pulse-animation");
        }, 300);
    }

    if(existente){
        existente.cantidad++;
    }else{
        carrito.push({
            id:id,
            nombre:nombre,
            precio:precio,
            cantidad:1
        });
    }
    actualizarCarrito();
}

function actualizarCarrito() {
    carritoDiv.innerHTML = "";
    let total = 0;
    let totalItems = 0;

    carrito.forEach((producto) => {
        const subtotal = producto.precio * producto.cantidad;
        total += subtotal;
        totalItems += producto.cantidad;

        carritoDiv.innerHTML += `
        <div class="card mb-2 border-0 bg-secondary bg-opacity-10 shadow-sm">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0 fw-bold text-truncate" style="max-width: 170px;">${producto.nombre}</h6>
                    <strong class="text-success">$${subtotal.toFixed(2)}</strong>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-1">
                        <button class="btn btn-sm btn-outline-danger rounded-circle p-0 d-flex align-items-center justify-content-center disminuir" data-id="${producto.id}" style="width: 26px; height: 26px;">
                            <i class="bi bi-dash"></i>
                        </button>
                        <span class="fw-bold px-2 small">${producto.cantidad}</span>
                        <button class="btn btn-sm btn-outline-success rounded-circle p-0 d-flex align-items-center justify-content-center aumentar" data-id="${producto.id}" style="width: 26px; height: 26px;">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                    <small class="text-muted small">$${producto.precio.toFixed(2)} c/u</small>
                </div>
            </div>
        </div>
        `;
    });

    // Actualizar insignia de ítems
    const cartCountBadge = document.getElementById("cart-count");
    if (cartCountBadge) {
        cartCountBadge.textContent = `${totalItems} ${totalItems === 1 ? 'ítem' : 'ítems'}`;
    }

    if(carrito.length == 0){
        carritoDiv.innerHTML = `
        <div class="text-center py-5 text-muted">
            <i class="bi bi-cart-x fs-1 d-block mb-2"></i>
            El carrito está vacío.
        </div>
        `;
    }

    totalDiv.innerHTML = "$"+total.toFixed(2);

    document.querySelectorAll(".aumentar").forEach(boton => {
        boton.onclick = () => {
            aumentarCantidad(
                boton.dataset.id
            );
        };
    });

    document.querySelectorAll(".disminuir").forEach(boton => {
        boton.onclick = () => {
            disminuirCantidad(
                boton.dataset.id
            );
        };
    });
}

function aumentarCantidad(id){
    const producto = carrito.find(p => p.id == id);
    if(!producto) return;

    const tarjeta = document.querySelector(`[data-id="${id}"]`);
    const stock = tarjeta ? parseInt(tarjeta.dataset.stock) : 0;

    if (producto.cantidad >= stock) {
        alert("No hay suficiente stock disponible.");
        return;
    }

    producto.cantidad++;
    if(producto.cantidad <=0){
        carrito = carrito.filter(p => p.id != id);
    }
    actualizarCarrito();
}

function disminuirCantidad(id){
    const producto = carrito.find(p => p.id == id);
    if(!producto) return;
    producto.cantidad--;
    if(producto.cantidad <=0){
        carrito = carrito.filter(p => p.id != id);
    }
    actualizarCarrito();
}

function mostrarMensaje(texto, tipo = "warning") {
    mensajeDiv.innerHTML = `
        <div class="alert alert-${tipo} alert-dismissible fade show">
            ${texto}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    setTimeout(() => {
        mensajeDiv.innerHTML = "";
    }, 3000);    
}

async function finalizarVenta() {
    console.log("Enviando venta...");

    const productos = carrito.map(producto => ({
        id: producto.id,
        cantidad: producto.cantidad
    }));

    const clienteNombre = clienteNombreInput ? clienteNombreInput.value.trim() : "Consumidor Final";
    const checkedRadio = document.querySelector('input[name="metodo-pago"]:checked');
    const metodoPago = checkedRadio ? checkedRadio.value : "transferencia";

    try {
        const respuesta = await fetch(
            "/ventas/api/finalizar/",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    cliente: clienteNombre || "Consumidor Final",
                    metodo_pago: metodoPago,
                    productos: productos
                })
            }
        );

        const datos = await respuesta.json();
        console.log("Respuesta de Django:", datos);

        if(datos.ok){
            actualizarStockTarjetas(datos.stock_actualizado);
            carrito = [];
            actualizarCarrito();
            mostrarMensaje(` Venta #${datos.venta} registrada correctamente`,
                "success"
            );
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

console.log("Asignando evento al botón");
botonFinalizar.onclick = finalizarVenta;

function actualizarStockTarjetas(stockActualizado) {
    if (!stockActualizado) return;
    stockActualizado.forEach(item => {
        const tarjeta = document.querySelector(
             `[data-id="${item.id}"]`
        );

        if(!tarjeta) return;
        tarjeta.dataset.stock = item.stock;

        const textoStock = tarjeta.querySelector(".texto-stock");

        if (textoStock) {
            if (item.stock === 0) {
                textoStock.innerHTML = "🔴 SIN STOCK";
                textoStock.className = "texto-stock text-danger fw-bold";
                tarjeta.style.opacity = "0.45";
            }
            else if (item.stock <= 5) {
                textoStock.innerHTML = `🟡 Stock: ${item.stock}`;
                textoStock.className = "texto-stock text-warning fw-bold";
                tarjeta.style.opacity = "1";
            }
            else {
                textoStock.innerHTML = `🟢 Stock: ${item.stock}`;
                textoStock.className = "texto-stock text-success fw-bold";
                tarjeta.style.opacity = "1";
            }
        }
    });
}




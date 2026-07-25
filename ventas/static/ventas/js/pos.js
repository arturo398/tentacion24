// Carrito de venta
let carrito = [];

// Elementos DOM
const carritoDiv = document.getElementById("carrito");
const totalDiv = document.getElementById("total");
const mensajeDiv = document.getElementById("mensaje-pos");
const botonFinalizar = document.getElementById("btn-finalizar");
const searchInput = document.getElementById("pos-search");
const clienteNombreInput = document.getElementById("cliente-nombre");
const posValorEnvioInput = document.getElementById("pos-valor-envio");
const categoriaBotones = document.querySelectorAll(".btn-categoria");
const productoCols = document.querySelectorAll(".producto-col");

if (posValorEnvioInput) {
    posValorEnvioInput.addEventListener("input", () => {
        actualizarCarrito();
    });
}

let categoriaSeleccionada = "todos";
let textoBusqueda = "";

// Filtrado de productos y combos
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
            b.classList.remove("btn-dark", "btn-warning");
            b.classList.add("btn-outline-dark");
        });
        boton.classList.remove("btn-outline-dark");
        if (boton.dataset.categoria === "combos") {
            boton.classList.add("btn-warning");
        } else {
            boton.classList.add("btn-dark");
        }
        
        categoriaSeleccionada = boton.dataset.categoria;
        filtrarProductos();
    });
});

// Eventos tarjetas de productos
document.querySelectorAll(".producto-card").forEach(tarjeta => {
    const btnAdd = tarjeta.querySelector(".btn-add-prod");

    const handleAdd = (e) => {
        if (e) e.stopPropagation();

        const id = tarjeta.dataset.id;
        const nombreBase = tarjeta.dataset.nombre;
        const stockBase = parseInt(tarjeta.dataset.stock) || 0;

        const selectPres = tarjeta.querySelector(".select-presentacion");
        let presNombre = "";
        let unidadesPack = 1;
        let precioItem = parseFloat(tarjeta.dataset.precio);

        if (selectPres) {
            const opt = selectPres.options[selectPres.selectedIndex];
            unidadesPack = parseInt(opt.dataset.unidades) || 1;
            precioItem = parseFloat(opt.dataset.precio);
            const presLabel = opt.dataset.nombre;
            presNombre = presLabel !== "Unidad suelta" ? ` [${presLabel}]` : "";
        }

        agregarAlCarrito({
            id: id,
            nombreKey: `${id}_pres_${unidadesPack}`,
            nombre: `${nombreBase}${presNombre}`,
            precio: precioItem,
            unidadesPack: unidadesPack,
            stockBase: stockBase,
            esCombo: false
        });
    };

    if (btnAdd) btnAdd.addEventListener("click", handleAdd);
    tarjeta.addEventListener("click", (e) => {
        if (!e.target.closest("select")) {
            handleAdd(e);
        }
    });
});

// Eventos tarjetas de combos
document.querySelectorAll(".combo-card").forEach(tarjeta => {
    const handleAddCombo = (e) => {
        if (e) e.stopPropagation();

        const id = tarjeta.dataset.id;
        const nombre = tarjeta.dataset.nombre;
        const precio = parseFloat(tarjeta.dataset.precio);
        const stockCombo = parseInt(tarjeta.dataset.stock) || 0;

        agregarAlCarrito({
            id: id,
            nombreKey: `combo_${id}`,
            nombre: `🍹 Promo: ${nombre}`,
            precio: precio,
            unidadesPack: 1,
            stockBase: stockCombo,
            esCombo: true
        });
    };

    tarjeta.addEventListener("click", handleAddCombo);
});

function agregarAlCarrito(itemData) {
    const existente = carrito.find(p => p.nombreKey === itemData.nombreKey);
    const cantidadDeseadaAct = existente ? existente.cantidad + 1 : 1;
    const unidadesDeseadasTotales = cantidadDeseadaAct * itemData.unidadesPack;

    if (unidadesDeseadasTotales > itemData.stockBase) {
        alert("No hay suficiente stock disponible para agregar esta cantidad.");
        return;
    }

    if (existente) {
        existente.cantidad++;
    } else {
        carrito.push({
            id: itemData.id,
            nombreKey: itemData.nombreKey,
            nombre: itemData.nombre,
            precio: itemData.precio,
            unidadesPack: itemData.unidadesPack,
            stockBase: itemData.stockBase,
            esCombo: itemData.esCombo,
            cantidad: 1
        });
    }

    actualizarCarrito();
}

function actualizarCarrito() {
    carritoDiv.innerHTML = "";
    let subtotalProductos = 0;
    let totalItems = 0;
    const valorEnvio = parseFloat(posValorEnvioInput ? posValorEnvioInput.value : 0) || 0;

    carrito.forEach((producto) => {
        const subtotal = producto.precio * producto.cantidad;
        subtotalProductos += subtotal;
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
                        <button class="btn btn-sm btn-outline-danger rounded-circle p-0 d-flex align-items-center justify-content-center disminuir" data-key="${producto.nombreKey}" style="width: 26px; height: 26px;">
                            <i class="bi bi-dash"></i>
                        </button>
                        <span class="fw-bold px-2 small">${producto.cantidad}</span>
                        <button class="btn btn-sm btn-outline-success rounded-circle p-0 d-flex align-items-center justify-content-center aumentar" data-key="${producto.nombreKey}" style="width: 26px; height: 26px;">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                    <small class="text-muted small">$${producto.precio.toFixed(2)} c/u</small>
                </div>
            </div>
        </div>
        `;
    });

    const cartCountBadge = document.getElementById("cart-count");
    if (cartCountBadge) {
        cartCountBadge.textContent = `${totalItems} ${totalItems === 1 ? 'ítem' : 'ítems'}`;
    }

    if (carrito.length === 0) {
        carritoDiv.innerHTML = `
        <div class="text-center py-5 text-muted">
            <i class="bi bi-cart-x fs-1 d-block mb-2"></i>
            El carrito está vacío.
        </div>
        `;
    }

    const totalFinal = subtotalProductos + valorEnvio;
    totalDiv.innerHTML = "$" + totalFinal.toFixed(2);

    document.querySelectorAll(".aumentar").forEach(boton => {
        boton.onclick = () => aumentarCantidad(boton.dataset.key);
    });

    document.querySelectorAll(".disminuir").forEach(boton => {
        boton.onclick = () => disminuirCantidad(boton.dataset.key);
    });
}

function aumentarCantidad(nombreKey) {
    const producto = carrito.find(p => p.nombreKey === nombreKey);
    if (!producto) return;

    if ((producto.cantidad + 1) * producto.unidadesPack > producto.stockBase) {
        alert("No hay suficiente stock disponible.");
        return;
    }

    producto.cantidad++;
    actualizarCarrito();
}

function disminuirCantidad(nombreKey) {
    const producto = carrito.find(p => p.nombreKey === nombreKey);
    if (!producto) return;

    producto.cantidad--;
    if (producto.cantidad <= 0) {
        carrito = carrito.filter(p => p.nombreKey !== nombreKey);
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
    }, 4000);
}

async function finalizarVenta() {
    if (carrito.length === 0) {
        alert("El carrito está vacío.");
        return;
    }

    const payloadProductos = carrito.map(item => ({
        id: item.id,
        cantidad: item.cantidad,
        unidades_pack: item.unidadesPack,
        precio: item.precio,
        es_combo: item.esCombo
    }));

    const clienteNombre = clienteNombreInput ? clienteNombreInput.value.trim() : "Consumidor Final";
    const checkedRadio = document.querySelector('input[name="metodo-pago"]:checked');
    const metodoPago = checkedRadio ? checkedRadio.value : "transferencia";
    const valorEnvio = parseFloat(posValorEnvioInput ? posValorEnvioInput.value : 0) || 0;

    botonFinalizar.disabled = true;
    botonFinalizar.textContent = "Procesando...";

    try {
        const respuesta = await fetch("/ventas/api/finalizar/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                cliente: clienteNombre || "Consumidor Final",
                metodo_pago: metodoPago,
                valor_envio: valorEnvio,
                productos: payloadProductos
            })
        });

        const datos = await respuesta.json();

        if (datos.ok) {
            actualizarStockTarjetas(datos.stock_actualizado);
            carrito = [];
            if (posValorEnvioInput) posValorEnvioInput.value = "0.00";
            actualizarCarrito();
            mostrarMensaje(`🎉 Venta #${datos.venta} registrada correctamente. ¡Stock actualizado!`, "success");
        } else {
            alert("Error al procesar la venta: " + datos.error);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Ocurrió un error de red al intentar finalizar la venta.");
    } finally {
        botonFinalizar.disabled = false;
        botonFinalizar.innerHTML = `<i class="bi bi-check-lg"></i> Finalizar Venta`;
    }
}

botonFinalizar.onclick = finalizarVenta;

function actualizarStockTarjetas(stockActualizado) {
    if (!stockActualizado) return;
    stockActualizado.forEach(item => {
        const tarjeta = document.querySelector(`.producto-card[data-id="${item.id}"]`);
        if (!tarjeta) return;

        tarjeta.dataset.stock = item.stock;
        const textoStock = tarjeta.querySelector(".texto-stock");

        if (textoStock) {
            if (item.stock === 0) {
                textoStock.innerHTML = `<i class="bi bi-x-circle-fill"></i> SIN STOCK`;
                textoStock.className = "texto-stock text-danger fw-bold mb-2 small";
                tarjeta.classList.add("opacity-50");
            } else if (item.stock <= 5) {
                textoStock.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> STOCK BAJO: ${item.stock} u.`;
                textoStock.className = "texto-stock text-warning fw-bold mb-2 small";
                tarjeta.classList.remove("opacity-50");
            } else {
                textoStock.innerHTML = `<i class="bi bi-check-circle-fill"></i> STOCK: ${item.stock} u.`;
                textoStock.className = "texto-stock text-success fw-bold mb-2 small";
                tarjeta.classList.remove("opacity-50");
            }
        }
    });
}

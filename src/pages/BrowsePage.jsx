import { useEffect, useState } from "react";
import {Link} from "react-router";

function BrowsePage() {
     const [products, setProducts] =  useState([]);
     const [page, setpage] = useState(1);
    useEffect(() => {
        async function loadProducts() {
            const skip = (page - 1) * 10;
            const response = await fetch(`https://dummyjson.com/products?limit=10&skip=${skip}`);
            const data = await response.json();
            setProducts(data.products)
            
        }
        loadProducts();
        
    }, [page]);

        return (
        <>
        <button disabled = {page === 1} onClick = {() => setpage(page - 1)}>Previous</button>
        <span> Page {page}</span>
        <button onClick={() => setpage(page + 1)}>Next</button>
       
       

        <ul>
            {products.map((product) => (
                <li 
                key = {product.id}>
                    <img src = {product.thumbnail}></img>
                    <h3>{product.title}</h3>
                    <p>Price: ${product.price}</p>
                    <Link to = {`/products/${product.id}`}> View Details </Link>
            

                    </li>
            ))}
        </ul>
        </>
        
    );
}
    



export default BrowsePage;
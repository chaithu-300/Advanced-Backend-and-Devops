import {useState, useEffect} from "react";
import {useParams, Link} from "react-router";

function ProductDetailPage() {
    const {id} = useParams();
    const[products, setProducts] = useState([]);

    useEffect(() => {
        async function loadProducts() {
            const res = await fetch(`https://dummyjson.com/products/${id}`);
            const data = await res.json();
            
            setProducts(data);
        }
        loadProducts();
    }, [id]);

    if (!products) {
        return <p>Loading...</p>
    }

    return(
        <>
        <ul>
            <Link to = "/"> Back to products</Link>
            {products.map((product) => (
                <li key={product.id}>
                    <h2>Title - {product.title}</h2>
                    <h2>Images</h2>
                    {product.images.map((image) => (
                        <img key = {image} src = {image} width = "150"/>
                    ))}

                    <h2>Reviews</h2>
                    <ul>
                        {product.reviews.map((review) => (
                            <li key = {review.reviewerEmail}>
                                {review.reviewerName} ({review.rating}/5): {review.comment}
                            </li>
                        ))}
                    </ul>

                    <p>Description - {product.description}</p>
                    <p>Price - ${product.price}</p>
                    <p>Stock - {product.stock}</p>
                    <p>Ratings - {product.rating}</p>
                    <p>Category - {product.category}</p>
                    
                
                </li>

            ))}
        </ul>
        </>
    )

}

export default ProductDetailPage
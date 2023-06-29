import React from 'react';

const Footer = () => {
  return (
    <footer>
      <div class="container text-center text-white pt-5 pb-5 mt-5">
        <div class="row">
          <div class="col-12 col-md-6 columnContent">
            <h2 class="mb-3">Scissor</h2>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
              enim ad minim veniam, quis nostrud exercitation ullamco laboris
              nisi ut aliquip ex ea commodo consequat.
            </p>
          </div>
         
          <div class="col-12 col-md-6 columnContent">
            <h2 class="mb-3">Quick Links</h2>
            <ul>
              <>
              <li><a href='www.github.com/spartan124'>Github</a></li>
              </>
              <>
              <li><a href ='www.twitter.com/jer_ryO'>Twitter</a></li>
              </>
              <>
              <li><a href ='www.linkedin.com/in/jerrylyte'>LinkedIn</a></li>
              </>
            </ul>
          </div>
           
        </div>
      </div>
    </footer>
  );
};

export default Footer;

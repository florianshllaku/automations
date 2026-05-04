"use client"

import { useEffect, useRef } from "react"
import * as THREE from "three"

interface BendLogoProps {
  src?: string
  className?: string
}

export function BendLogo({ src = "/images/logo.png", className = "" }: BendLogoProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Scene setup
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    )
    camera.position.z = 5

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(container.clientWidth, container.clientHeight)
    renderer.setClearColor(0x000000, 0)
    container.appendChild(renderer.domElement)

    // Load the logo texture
    const textureLoader = new THREE.TextureLoader()
    let mesh: THREE.Mesh | null = null
    let planeAspect = 4 // default aspect ratio while loading

    // Mouse tracking
    const mouse = new THREE.Vector2(0, 0)
    const mouseTarget = new THREE.Vector2(0, 0)

    // Shader uniforms
    const uniforms = {
      uTexture: { value: null as THREE.Texture | null },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uTime: { value: 0 },
      uBend: { value: 0 }, // 0 = flat, 1 = bent
      uHover: { value: 0 }, // 0 to 1 smooth hover intensity
    }

    const vertexShader = `
      uniform vec2 uMouse;
      uniform float uTime;
      uniform float uBend;
      uniform float uHover;
      varying vec2 vUv;

      void main() {
        vUv = uv;
        vec3 pos = position;

        // Distance from this vertex to the mouse in UV space
        float dist = distance(uv, uMouse);

        // Moderate bulge effect: vertices close to cursor pop toward camera
        float bulge = exp(-dist * 5.0) * uHover;
        pos.z += bulge * 1.1;

        // Subtle ambient wave across the whole plane
        float wave = sin(pos.x * 3.0 + uTime * 1.2) * cos(pos.y * 3.0 + uTime * 0.8);
        pos.z += wave * 0.04 * uBend;

        // Gentle plane tilt toward cursor
        vec2 bendDir = (uMouse - vec2(0.5)) * 2.0;
        pos.z += (pos.x * bendDir.x + pos.y * bendDir.y) * 0.22 * uHover;

        // Subtle radial pinch around cursor
        vec2 toMouse = uv - uMouse;
        float pinchFalloff = exp(-dist * 5.0) * uHover;
        pos.x += toMouse.x * pinchFalloff * 0.06;
        pos.y += toMouse.y * pinchFalloff * 0.06;

        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
      }
    `

    const fragmentShader = `
      uniform sampler2D uTexture;
      varying vec2 vUv;

      void main() {
        // Sample the texture directly — no color shift, no chromatic aberration
        vec4 color = texture2D(uTexture, vUv);
        gl_FragColor = color;
      }
    `

    const updatePlaneSize = () => {
      if (!mesh) return
      // Fit the plane in the camera frustum based on logo aspect
      const fovRad = (camera.fov * Math.PI) / 180
      const distance = camera.position.z
      const viewportHeight = 2 * Math.tan(fovRad / 2) * distance
      const viewportWidth = viewportHeight * camera.aspect

      // Choose plane size — contain within 95% of viewport (larger logo)
      const maxWidth = viewportWidth * 0.95
      const maxHeight = viewportHeight * 0.95

      let planeWidth = maxWidth
      let planeHeight = planeWidth / planeAspect
      if (planeHeight > maxHeight) {
        planeHeight = maxHeight
        planeWidth = planeHeight * planeAspect
      }

      mesh.scale.set(planeWidth, planeHeight, 1)
    }

    textureLoader.load(
      src,
      (texture) => {
        texture.minFilter = THREE.LinearFilter
        texture.magFilter = THREE.LinearFilter
        texture.generateMipmaps = false
        uniforms.uTexture.value = texture
        planeAspect = texture.image.width / texture.image.height

        // Create geometry with high subdivision for smooth bending
        const geometry = new THREE.PlaneGeometry(1, 1, 128, 128)
        const material = new THREE.ShaderMaterial({
          uniforms,
          vertexShader,
          fragmentShader,
          transparent: true,
        })

        mesh = new THREE.Mesh(geometry, material)
        scene.add(mesh)
        updatePlaneSize()

        // Fade in the bend on load
        let bendProgress = 0
        const fadeIn = () => {
          bendProgress = Math.min(bendProgress + 0.01, 1)
          uniforms.uBend.value = bendProgress
          if (bendProgress < 1) {
            requestAnimationFrame(fadeIn)
          }
        }
        fadeIn()
      },
    )

    // Event handlers
    const handlePointerMove = (e: PointerEvent) => {
      const rect = container.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width
      const y = 1.0 - (e.clientY - rect.top) / rect.height
      mouseTarget.set(x, y)
    }

    const handlePointerEnter = () => {
      // Animate hover intensity up
    }

    const handleResize = () => {
      camera.aspect = container.clientWidth / container.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(container.clientWidth, container.clientHeight)
      updatePlaneSize()
    }

    window.addEventListener("pointermove", handlePointerMove)
    window.addEventListener("resize", handleResize)
    container.addEventListener("pointerenter", handlePointerEnter)

    // Animation loop
    const clock = new THREE.Clock()
    let frameId = 0
    let hoverTarget = 1 // always engaged, mouse drives the look

    const animate = () => {
      frameId = requestAnimationFrame(animate)
      uniforms.uTime.value = clock.getElapsedTime()

      // Smooth mouse interpolation
      mouse.lerp(mouseTarget, 0.08)
      uniforms.uMouse.value.copy(mouse)

      // Smooth hover intensity
      uniforms.uHover.value += (hoverTarget - uniforms.uHover.value) * 0.05

      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(frameId)
      window.removeEventListener("pointermove", handlePointerMove)
      window.removeEventListener("resize", handleResize)
      container.removeEventListener("pointerenter", handlePointerEnter)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      renderer.dispose()
      if (mesh) {
        mesh.geometry.dispose()
        ;(mesh.material as THREE.ShaderMaterial).dispose()
      }
      if (uniforms.uTexture.value) {
        uniforms.uTexture.value.dispose()
      }
    }
  }, [src])

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ width: "100%", height: "100%" }}
    />
  )
}
